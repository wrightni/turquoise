from app import app
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
import base64
import io
import json
import collections
from PIL import Image
from osgeo import gdal
import pandas as pd
import numpy as np

from datetime import datetime, timedelta

# app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
cache.init_app(app)

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    validations = db.relationship('Points', backref='author', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Points(db.Model):

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    point_id = db.Column(db.Integer, db.ForeignKey('validation.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    clsf = db.Column(db.Text)

    def __repr__(self):
        return '<ID {}>'.format(self.id)

class Validation(db.Model):
    # Database for storing training / validation data
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # image_id
    image_id = db.Column(db.Integer, db.ForeignKey('images.id'))
    image_x = db.Column(db.Integer)
    image_y = db.Column(db.Integer)
    date = db.Column(db.DateTime)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    
    def __repr__(self):
        return '<ID {}>'.format(self.id)


class Images(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    image_name = db.Column(db.Text)

    def __repr__(self):
        return '<Name {}>'.format(self.image_name)


db.create_all()
db.session.commit()
print("created")

@app.route("/")
@app.route("/overview")
def overview():

    return render_template(
        'overview.html',
    ).encode(encoding='UTF-8')


@app.route("/classifier")
def classifier():

    proj, window_ul, encoded_img_data = load_image()

    cache.set("window_ul", window_ul)

    val_existing = Validation.query.filter(Validation.image_id == 1, 
                                           Validation.image_x.between(window_ul[0], window_ul[0]+512),
                                           Validation.image_y.between(window_ul[1], window_ul[1]+512))

    preset_deque = collections.deque([(v.image_x - window_ul[0], v.image_y - window_ul[1]) for v in val_existing])

    ##for val in val_existing:
     #   preset_deque.append((val.))

    cache.set("preset_deque", preset_deque)

    return render_template(
        'classifier.html', image=encoded_img_data.decode('utf-8')
    ).encode(encoding='UTF-8')


@app.route("/assign", methods=['POST'])
def assign():

    user_id = 0
    image_id = 1

    # Get the window location to place the assigned value in the global image coordinates
    window_ul = cache.get("window_ul")

    jsdata = request.get_json()
    window_x = jsdata['x']
    window_y = jsdata['y']

    abs_x = window_ul[0] + window_x
    abs_y = window_ul[1] + window_y

    # check if point exists in Validation
    exists = Validation.query.filter_by(image_id=image_id, image_x=abs_x, image_y=abs_y).first()
    if not exists:
        new_valpt = Validation(image_id=image_id, 
                            image_x=abs_x, image_y=abs_y, 
                            date=datetime.utcnow(), lat=90, lon=180, 
                            )
        db.session.add(new_valpt)
        #db.session.commit()
        db.session.flush()
        # this gets assigned when the insert is commited above
        #point_id = new_valpt.id
        point_id = new_valpt.id
    else:
        point_id = exists.id

    print(point_id)
    # add new point to Points
    new_point = Points(user_id=user_id, point_id=point_id, clsf=jsdata['clsf'])

    db.session.add(new_point)
    db.session.commit()
 
    results = {'processed': 'true'}
    return jsonify(results)


@app.route("/get_preset", methods=['GET'])
def get_preset():
    
    preset_deque = cache.get("preset_deque")

    try:
        x, y = preset_deque.popleft()
    except IndexError:
        x, y = 0, 0
        success = False
    else:
        cache.set("preset_deque", preset_deque)
        success = True

    print(preset_deque)

    return jsonify({'success': success, 'x': x, 'y': y})


def load_image():

    DISPLAY_SIZE = int(512)

    ds = gdal.Open('app/static/2016_07_19_02134.JPG', gdal.GA_ReadOnly)

    x_dim = ds.RasterXSize
    y_dim = ds.RasterYSize

    rng = np.random.default_rng()

    # If the image is smaller than the default display, chose the largest square that fits
    if x_dim <= DISPLAY_SIZE: 
        DISPLAY_SIZE = x_dim
        x = 0
    else:
        print(x_dim, DISPLAY_SIZE)
        x = int(rng.integers(x_dim - DISPLAY_SIZE))
    
    if y_dim <= DISPLAY_SIZE:
        DISPLAY_SIZE = y_dim
        y = 0
    else:
        y = int(rng.integers(y_dim - DISPLAY_SIZE))

    a = ds.ReadAsArray(x, y, DISPLAY_SIZE, DISPLAY_SIZE)

    img = Image.fromarray(reshape_bxy2yxb(ds.ReadAsArray(x, y, DISPLAY_SIZE, DISPLAY_SIZE)))

    # Save the upper left coordinates of this current window
    window_ul = [x, y]

    # Create an in-memory file object
    file_object = io.BytesIO()
    img.save(file_object, 'PNG')

    #file_object.seek(0)

    encoded_img_data = base64.b64encode(file_object.getvalue())

    # for saving lat/lon information
    proj = ds.GetProjection()
    gt = ds.GetGeoTransform()

    ds = None

    return proj, window_ul, encoded_img_data


def select_validation_pixel(x_dim, y_dim):

    rng = np.random.default_rng()
    x = rng.integers(int(x_dim*.1), int(x_dim*.9))
    y = rng.integers(int(y_dim*.1), int(y_dim*.9))

    return x, y


def reshape_bxy2yxb(img_data, dtype=np.uint8):
    bands, x, y = np.shape(img_data)

    new_img = np.zeros((x, y, bands), dtype=dtype)
    for b in range(bands):
        new_img[:, :, b] = img_data[b, :, :]

    return new_img