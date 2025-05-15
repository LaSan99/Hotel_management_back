from flask import Flask
from flask_pymongo import PyMongo
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from routes import init_routes

app = Flask(__name__)
CORS(app)

# Use your MongoDB URI (local or Atlas)
app.config["MONGO_URI"] = "mongodb://localhost:27017/hotel_booking_flask"
app.config["JWT_SECRET_KEY"] = "super-secret"  # Use a .env in production

mongo = PyMongo(app)
jwt = JWTManager(app)

from routes import init_routes
init_routes(app, mongo)

if __name__ == '__main__':
    app.run(debug=True, port=5050)

# venv\Scripts\activate