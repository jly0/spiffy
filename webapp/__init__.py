'''TODO:
    -need to create a celerybeat to check up on endpoints
    -need to parametize worker scripts
    -need to create a front end
    -need to finish the dockerfile crappiolioio

   Open thoughts:
    -Do i want to use redis as a broker
    -how in the world do i add authentication
'''


from flask_bootstrap import Bootstrap
import os 
import random
import time
from flask import Flask, request, render_template, session, flash, redirect, url_for, jsonify, g
from celery import Celery
import json
import requests
import configparser
from flask_restful import Resource, Api, reqparse
import shelve
from . import celeryconfig
#from . import celerycontrol


#initialize flask, celery

app = Flask(__name__)
bs = Bootstrap(app)
api = Api(app)
#app.config.from_object('config')


# Celery configuration
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)
celery.config_from_object(celeryconfig)



#inititialize Shelf
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = shelve.open("endpoints.db",writeback=True)
    return db

def extract_shelf_data():
    endpoints = []
    shelf = shelve.open('endpoints.db')
    for item in shelf:
        endpoints.append(shelf[item])
    return endpoints


@app.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


#app single page
@app.route('/')
def index():
    endpoints = extract_shelf_data()
    return render_template('index.html',endpoints=endpoints)



class endpoints(Resource):
    def get(self):
        shelf = get_db()
        keys = list(shelf.keys())

        endpoints = []

        for key in keys:
            endpoints.append(shelf[key])

        return {'message': 'Success', 'data': endpoints}, 200

    def post(self):
        parser = reqparse.RequestParser()

        parser.add_argument('endpoint', required=True)
        parser.add_argument('worker', required=True)
        parser.add_argument('boolean', required=False)
        parser.add_argument('value', required=False)
        parser.add_argument('href',required=False)

        # Parse the arguments into an object
        args = parser.parse_args()
        args['boolean'] = args['boolean'].lower()
        if args['boolean'] != 'true' and args['boolean'] != 'false':
            args['boolean'] = 'true'
        shelf = get_db()
        '''try:
            if shelf[args['endpoint']]:
                return {'message':'Endpoint already exists'}, 403
        except:
            pass'''
        
        shelf[args['endpoint']] = args
        return {'message': 'Endpoint added', 'data': args}, 201

class endpoint(Resource):
    def get(self, endpoint):
        shelf = get_db()

        # If the key does not exist in the data store, return a 404 error.
        if not (endpoint in shelf):
            return {'message': 'Endpoint not found', 'data': {}}, 404

        return {'message': 'Endpoint found', 'data': shelf[endpoint]}, 200

    def delete(self, endpoint):
        shelf = get_db()

        # If the key does not exist in the data store, return a 404 error.
        if not (endpoint in shelf):
            return {'message': 'Endpoint not found', 'data': {}}, 404

        del shelf[endpoint]
        return {'message':'Endpoint deleted', 'data':{}}, 200

    def patch(self,endpoint):
        shelf = get_db()
        parser = reqparse.RequestParser()

        parser.add_argument('worker', required=False)
        parser.add_argument('boolean', required=False)
        parser.add_argument('value', required=False)
        parser.add_argument('href',required=False)

        args = parser.parse_args()
        for arg in args.keys():
            if args[arg] != None:
                shelf[endpoint][arg] = args[arg]
                print (args[arg])
                print (shelf[endpoint][arg])

        return {'message': 'Endpoint updated', 'data': shelf[endpoint]} , 200
                


api.add_resource(endpoints, '/endpoints')
api.add_resource(endpoint, '/endpoint/<string:endpoint>')
