from flask import Flask
from flask_pymongo import PyMongo
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from routes import init_routes
import os

app = Flask(__name__)
CORS(app)

# Use environment variable for MongoDB URI
app.config["MONGO_URI"] = os.environ.get("MONGODB_URI", "mongodb+srv://lasannavodya:DelLCS5EiIBT3jFu@course.uf2pi.mongodb.net/hotel_booking_flask?retryWrites=true&w=majority&appName=Course")
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "super-secret")  # Use environment variable in production

mongo = PyMongo(app)
jwt = JWTManager(app)

from routes import init_routes
init_routes(app, mongo)

# For local development
if __name__ == '__main__':
    app.run(debug=True, port=5050) 