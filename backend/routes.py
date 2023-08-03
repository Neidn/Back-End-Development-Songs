from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service is None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"

print(f"connecting to url: {url}")

client = None

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

if client is None:
    app.logger.error('MongoDB connection error')
    # abort(500, 'MongoDB connection error')
    sys.exit(1)

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)


def parse_json(data):
    return json.loads(json_util.dumps(data))


######################################################################
# INSERT CODE HERE
######################################################################

# GET /health
# Returns: 200 OK
@app.route("/health")
def health():
    """Check the service health"""
    return make_response(jsonify(status="OK"), 200)


# GET /count
# Returns: 200 OK
@app.route("/count")
def count():
    """Count the number of songs"""
    cnt = db.songs.count_documents({})
    return make_response(jsonify(count=cnt), 200)


# GET /song
# Returns: 200 OK, 404 Not Found
@app.route("/song", methods=["GET"])
def get_songs():
    """Retrieve a list of songs"""
    songs = db.songs.find({})
    if songs:
        return make_response(jsonify(parse_json(songs)), 200)
    else:
        return make_response(jsonify(status="Not Found"), 404)


# GET /song/<id>
# Returns: 200 OK, 404 Not Found
@app.route("/song/<int:song_id>", methods=["GET"])
def get_song(song_id):
    """Retrieve a single song"""
    song = db.songs.find_one({"id": song_id})
    if song:
        return make_response(jsonify(parse_json(song)), 200)
    else:
        return make_response(jsonify(status="Not Found"), 404)


# POST /song
# Returns: 201 Created, 400 Bad Request, 302 Found
@app.route("/song", methods=["POST"])
def create_song():
    """Create a new song"""
    if not request.json:
        abort(400, "Bad Request")

    song = request.get_json()
    if song["id"] < 0:
        abort(400, "Bad Request")

    if db.songs.find_one({"id": song["id"]}):
        return make_response(jsonify(
            {"Message": f"song with id {song['id']} already present"}
        ), 302)
    else:
        db.songs.insert_one(song)

        return make_response(jsonify(
            {
                "inserted id": {'$oid': str(song['_id'])},
            }
        ), 201)
