#!/usr/bin/env python3
'''
Script for generating .svg best cut schema
All units are in mm
'''

# Imports
import sys
import os
import json
import math
import numpy
import itertools
from flask import Flask #pip3 install Flask
from flask import flash, redirect, render_template, request, session, abort, Response, send_from_directory

# Global variables
app = Flask(__name__)


# Class declarations
class Segment:
  def __init__(self, x1, y1, x2, y2):
    self.x1 = x1;
    self.y1 = y1;
    self.x2 = x2;
    self.y2 = y2;
    self.A = (y1-y2)
    self.B = (x2-x1)
    self.C = -1*(x1*y2 - x2*y1)
  def intersect(self, segment):
    if not isinstance(segment, Segment):
      raise(TypeError("Oh no no"))
    D  = self.A * segment.B - self.B * segment.A
    Dx = self.C * segment.B - self.B * segment.C
    Dy = self.A * segment.C - self.C * segment.A
    if D != 0:
      x = Dx / D
      y = Dy / D
      if (x<self.x1 or self.x2<x) and (x<self.x2 or self.x1<x) or \
      (y<self.y1 or self.y2<y) and (y<self.y2 or self.y1<y) or \
      (x<segment.x1 or segment.x2<x) and (x<segment.x2 or segment.x1<x) or \
      (y<segment.y1 or segment.y2<y) and (y<segment.y2 or segment.y1<y):
        return None;
      #print ("Intersection between segment " + str(self) + " and " + str(segment)+" is "+ str(x)+ "," +str(y))
      return (x,y)
    else:
      return None
  def __str__(self):
    return "("+str(self.x1)+", "+str(self.y1)+" --> "+str(self.x2)+", "+str(self.y2)+")"
  def __repr__(self):
    return self.__str__()


# Function declarations
def shapesToSVG(req, layout):
    '''
    '''
    result = '<svg width="'+str(req["width"])+'" height="'+str(req["height"])+'">' + '\n'
    result += '<rect width="'+str(req["width"])+'" height="'+str(req["height"])+'" style="fill:burlywood" />' + '\n'
    for piece in layout:
        result += '<g transform="translate('+str(piece["origin"]["x"])+','+str(piece["origin"]["y"])+')">' + '\n'
        result += '  <rect width="'+str(piece["size"]["x"])+'" height="'+str(piece["size"]["y"])+'" style="fill:rgb(0,0,255);stroke-width:1;stroke:rgb(0,0,0)" />' + '\n'
        result += '</g>' + '\n'
    result += '</svg>' + '\n'
    return result

def compose(req, order, rot):
    '''
    '''
    def distance(p, q):
        '''
        For any dimension space
        d(p,q) = sqrt((q_x-p_x)^2 + (q_y-p_y)^2)
        '''
        return math.sqrt(numpy.sum(numpy.subtract(q, p) ** 2))

    def selectBestTranslation(req, layout, elem):
        '''       
        Performs analisys over the layout to select the best fit for the new elem

        :param req: The request obj
        :param layout: The current layout: A list of shapes that are dicts of origins and sizes
        :param elem: The new element to allocate: dict with width and height
        :return: returns an array [x, y] with the best translation for this object
        '''
        result = [req["width"], req["height"]];
        for degree in range(0,91):
          start = [req["clearance"], req["clearance"]]
          end = [req["width"], math.tan(math.radians(degree))*req["width"]]
          if end[1] > req["height"]: 
            end[0] = req["height"]/math.tan(math.radians(degree))
            end[1] = req["height"]
          segment = Segment(start[0],start[1],end[0],end[1])
          
          print(str(degree)+" Segment "+str(segment))
          
          for shape in layout:
            n = Segment(shape["origin"]["x"], shape["origin"]["y"], shape["origin"]["x"] + shape["size"]["x"], shape["origin"]["y"])
            e = Segment(shape["origin"]["x"] + shape["size"]["x"], shape["origin"]["y"], shape["origin"]["x"] + shape["size"]["x"], shape["origin"]["y"] + shape["size"]["y"])
            s = Segment(shape["origin"]["x"] + shape["size"]["x"], shape["origin"]["y"] + shape["size"]["y"], shape["origin"]["x"], shape["origin"]["y"] + shape["size"]["y"])
            w = Segment(shape["origin"]["x"], shape["origin"]["y"] + shape["size"]["y"], shape["origin"]["x"], shape["origin"]["y"])
            print("Lets see")

            pt = segment.intersect(e)
            if pt: 
              #print("   Segment e "+str(e))
              if (distance([0,0], pt)<distance([0,0], result)):
                print("      found a better pt " + str(pt))
                result = pt
            pt = segment.intersect(s)
            if pt: 
              #print("   Segment s "+str(s))
              if (distance([0,0], pt)<distance([0,0], result)):
                print("      found a better pt " + str(pt))
                result = pt
           
        return result

    def layoutSize(layout):
        maxWidth = 0
        maxHeight = 0
        for shape in layout:
            if shape["origin"]["x"] + shape["size"]["x"] > maxWidth: maxWidth = shape["origin"]["x"] + shape["size"]["x"]
            if shape["origin"]["y"] + shape["size"]["y"] > maxHeight: maxHeight = shape["origin"]["y"] + shape["size"]["y"]
        return {"x":maxWidth, "y":maxHeight}

    layout = []
    for idx, elem in enumerate(order):
        if len(layout) > 0: 
            [x,y] = selectBestTranslation(req, layout, req["pieces"][elem])
        else:
            x=0
            y=0
        if rot[idx]:
            layout.append({"origin":{"x":x + req["clearance"], "y":y + req["clearance"]}, 
                           "size": {"x":req["pieces"][elem]["height"], "y":req["pieces"][elem]["width"]}})
        else:
            layout.append({"origin":{"x":x + req["clearance"], "y":y + req["clearance"]}, 
                           "size": {"x":req["pieces"][elem]["width"], "y":req["pieces"][elem]["height"]}})
        print ("layout: " + str(layout))
    #print ("layout diagonal: " + str(distance([0,0,0], [100,100,100])))
    return layout

def compute(req):
    '''
    This method processes all the possible combinations of the requested cuts 
    w/ and wo/ rotating the pieces 90 degrees
    '''
    result = ""
    print(json.dumps(req, indent=4, sort_keys=True))

    # Unroll to pieces list and rearrange the json
    req["clearance"] = float(req["clearance"])
    req["width"] = float(req["width"])
    req["height"] = float(req["height"])
    req["stockCount"] = int(req["stockCount"])
    req["pieces"] = []
    for cut in req["cuts"]:
        for i in range(0,int(cut["number"])):
            req["pieces"].append({"height":float(cut["height"]), "width":float(cut["width"])})
    del req["cuts"]

    print(json.dumps(req, indent=4, sort_keys=True))

    for perm in list(itertools.permutations(range(0,len(req["pieces"])), len(req["pieces"]))):
        for rotations in list(itertools.product([True, False], repeat = len(req["pieces"]))):

            print("Perm: " + str(perm) + ". Rot: " + str(rotations));
            layout = compose(req, perm, rotations)
            result += shapesToSVG(req, layout)
       
    #return shapesToSVG('')
    return result


@app.route("/cuts.svg", methods = ['POST'])
def makecuts():
    parsed = request.get_json()
    return Response(compute(parsed),
                    mimetype='image/svg+xml')

@app.route("/")
def hello():
    return render_template('form.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Main body
if __name__ == '__main__':
    #print(compute(json.loads('{"clearance": "0.1", "cuts": [{"height": "10", "number": "1", "width": "10"}, {"height": "20", "number": "1", "width": "20"}], "height": "297", "stockCount": "1", "width": "210"}')))
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)


