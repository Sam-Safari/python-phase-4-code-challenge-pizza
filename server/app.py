#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response, jsonify
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

# Create DB tables for testing and development if they don't exist
with app.app_context():
    db.create_all()

api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"


@app.route('/restaurants')
def get_restaurants():
    restaurants = Restaurant.query.all()
    # return only id, name, address for the list view
    data = [
        {
            'id': r.id,
            'name': r.name,
            'address': r.address
        }
        for r in restaurants
    ]
    return make_response(jsonify(data), 200)


@app.route('/restaurants/<int:id>', methods=['GET', 'DELETE'])
def handle_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if not restaurant:
        return make_response(jsonify({'error': 'Restaurant not found'}), 404)

    if request.method == 'GET':
        # include restaurant_pizzas and nested pizza data
        rps = []
        for rp in restaurant.restaurant_pizzas:
            rps.append({
                'id': rp.id,
                'pizza': {
                    'id': rp.pizza.id,
                    'name': rp.pizza.name,
                    'ingredients': rp.pizza.ingredients
                },
                'pizza_id': rp.pizza_id,
                'price': rp.price,
                'restaurant_id': rp.restaurant_id
            })

        data = {
            'id': restaurant.id,
            'name': restaurant.name,
            'address': restaurant.address,
            'restaurant_pizzas': rps
        }
        return make_response(jsonify(data), 200)

    if request.method == 'DELETE':
        db.session.delete(restaurant)
        db.session.commit()
        return ('', 204)


@app.route('/pizzas')
def get_pizzas():
    pizzas = Pizza.query.all()
    data = [
        {
            'id': p.id,
            'name': p.name,
            'ingredients': p.ingredients
        }
        for p in pizzas
    ]
    return make_response(jsonify(data), 200)


@app.route('/restaurant_pizzas', methods=['POST'])
def create_restaurant_pizza():
    data = request.get_json()
    try:
        rp = RestaurantPizza(
            price=data.get('price'),
            pizza_id=data.get('pizza_id'),
            restaurant_id=data.get('restaurant_id')
        )
        db.session.add(rp)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return make_response(jsonify({'errors': ['validation errors']}), 400)

    # include nested pizza and restaurant in response
    result = {
        'id': rp.id,
        'pizza': {
            'id': rp.pizza.id,
            'name': rp.pizza.name,
            'ingredients': rp.pizza.ingredients
        },
        'pizza_id': rp.pizza_id,
        'price': rp.price,
        'restaurant': {
            'id': rp.restaurant.id,
            'name': rp.restaurant.name,
            'address': rp.restaurant.address
        },
        'restaurant_id': rp.restaurant_id
    }
    return make_response(jsonify(result), 201)


if __name__ == "__main__":
    app.run(port=5555, debug=True)
