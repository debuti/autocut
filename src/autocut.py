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
    This method processes all the possible combinations of the requested cuts 
    w/ and wo/ rotating the pieces 90 degrees
    '''
    def distance(p, q):
        '''
        For any dimension space
        d(p,q) = sqrt((q_x-p_x)^2 + (q_y-p_y)^2)
        '''
        return math.sqrt(numpy.sum(numpy.subtract(q, p) ** 2))

    def layoutSize(layout):
        maxWidth = 0
        maxHeight = 0
        for shape in layout:
            if shape["origin"]["x"] + shape["size"]["x"] > maxWidth: maxWidth = shape["origin"]["x"] + shape["size"]["x"]
            if shape["origin"]["y"] + shape["size"]["y"] > maxHeight: maxHeight = shape["origin"]["y"] + shape["size"]["y"]
        return {"x":maxWidth, "y":maxHeight}

    layout = []
    for idx, elem in enumerate(order):
        lsize = layoutSize(layout)
        if rot[idx]:
            layout.append({"origin":{"x":lsize["x"] + req["clearance"], "y":lsize["y"] + req["clearance"]}, 
                           "size": {"x":req["pieces"][elem]["height"], "y":req["pieces"][elem]["width"]}})
        else:
            layout.append({"origin":{"x":lsize["x"] + req["clearance"], "y":lsize["y"] + req["clearance"]}, 
                           "size": {"x":req["pieces"][elem]["width"], "y":req["pieces"][elem]["height"]}})
        print ("layout: " + str(layout))
    lsize = layoutSize(layout)
    print ("layout diagonal: " + str(distance([0,0,0], [100,100,100])))
    return layout

def compute(req):
    '''
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
    print(compute(json.loads('{"clearance": "0.1", "cuts": [{"height": "10", "number": "1", "width": "10"}, {"height": "20", "number": "1", "width": "20"}], "height": "297", "stockCount": "1", "width": "210"}')))
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))


