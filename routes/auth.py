from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token

auth = Blueprint("auth", __name__)

def init_auth_routes(app, mongo):
    users = mongo.db.users

    @app.route("/auth/register", methods=["POST"])
    def register():
        data = request.get_json()
        
        # Check for required fields
        required_fields = ["email", "password", "name", "phone"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

        # Check if user already exists
        if users.find_one({"email": data["email"]}):
            return jsonify({"error": "User already exists"}), 400

        # Create new user document
        hashed = generate_password_hash(data["password"])
        new_user = {
            "email": data["email"],
            "password": hashed,
            "name": data["name"],
            "phone": data["phone"],
            "address": data.get("address", ""),  # Address is optional
            "is_admin": data.get("is_admin", False)  # Default to non-admin
        }
        
        # Insert the user into database
        users.insert_one(new_user)
        
        return jsonify({
            "message": "User registered successfully",
            "user": {
                "email": new_user["email"],
                "name": new_user["name"],
                "phone": new_user["phone"],
                "address": new_user["address"]
            }
        }), 201

    @app.route("/auth/login", methods=["POST"])
    def login():
        data = request.get_json()
        user = users.find_one({"email": data["email"]})
        if not user or not check_password_hash(user["password"], data["password"]):
            return jsonify({"error": "Invalid credentials"}), 401

        # Use email as identity and include admin status as additional claims
        token = create_access_token(
            identity=data["email"],
            additional_claims={"is_admin": user.get("is_admin", False)}
        )
        return jsonify({
            "access_token": token,
            "is_admin": user.get("is_admin", False),
            "user": {
                "email": user["email"],
                "name": user.get("name", ""),
                "phone": user.get("phone", ""),
                "address": user.get("address", "")
            }
        }), 200
