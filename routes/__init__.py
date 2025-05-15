from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from models import format_room, format_booking
from .auth import init_auth_routes
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

def init_routes(app, mongo):
    rooms = mongo.db.rooms
    bookings = mongo.db.bookings
    init_auth_routes(app, mongo)

    @app.route('/rooms', methods=['GET'])
    def get_rooms():
        all_rooms = rooms.find()
        return jsonify([format_room(r) for r in all_rooms])

    @app.route('/rooms/<room_id>', methods=['GET'])
    def get_room(room_id):
        room = rooms.find_one({"_id": ObjectId(room_id)})
        if not room:
            return jsonify({"error": "Room not found"}), 404
        return jsonify(format_room(room))

    @app.route('/rooms', methods=['POST'])
    def add_room():
        data = request.get_json()
        room = {
            "title": data["title"],
            "description": data["description"],
            "price": data["price"],
            "is_available": True,
            "type": data["type"],
            "images": data.get("images", [])  # Array of image URLs with default empty array
        }
        result = rooms.insert_one(room)
        created_room = rooms.find_one({"_id": result.inserted_id})
        return jsonify({"message": "Room created successfully", "room": format_room(created_room)}), 201

    @app.route('/rooms/<room_id>', methods=['DELETE'])
    def delete_room(room_id):
        rooms.delete_one({"_id": ObjectId(room_id)})
        return '', 204

    @app.route('/book', methods=['POST'])
    @jwt_required()
    def book_room():
        try:
            # Get user email from JWT token
            user_email = get_jwt_identity()
            if not user_email:
                return jsonify({"error": "Authentication required"}), 401

            # Get and validate request data
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 422

            print("Received booking data:", data)
            
            # Validate required fields
            required_fields = ['room_id', 'start_date', 'end_date', 'guest_name', 'guest_phone']
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 422
            
            # Get room information to calculate total price
            try:
                room_id = str(data["room_id"])
                room = rooms.find_one({"_id": ObjectId(room_id)})
                if not room:
                    return jsonify({"error": "Room not found"}), 404
            except Exception as e:
                print(f"Room lookup error: {str(e)}")
                return jsonify({"error": "Invalid room ID format"}), 422
                
            # Calculate total price based on number of days
            try:
                start_date = datetime.strptime(str(data["start_date"]), "%Y-%m-%d")
                end_date = datetime.strptime(str(data["end_date"]), "%Y-%m-%d")
                days = (end_date - start_date).days
                if days <= 0:
                    return jsonify({"error": "Check-out date must be after check-in date"}), 422
                total_price = days * room["price"]
            except ValueError as e:
                print(f"Date parsing error: {str(e)}")
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 422
            
            # Create booking document
            booking = {
                "room_id": ObjectId(room_id),
                "user_email": user_email,  # Use the email from JWT token
                "guest_name": str(data["guest_name"]).strip(),
                "guest_phone": str(data["guest_phone"]).strip(),
                "num_guests": int(data.get("num_guests", 1)),
                "start_date": data["start_date"],
                "end_date": data["end_date"],
                "special_requests": str(data.get("special_requests", "")).strip(),
                "total_price": total_price,
                "payment_method": str(data.get("payment_method", "Credit Card")),
                "status": "Booked",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            print("Creating booking:", booking)
            
            # Insert booking into database
            result = bookings.insert_one(booking)
            
            # Prepare response
            response_data = {
                "booking_id": str(result.inserted_id),
                "total_price": total_price,
                "message": "Booking successful",
                "status": "Booked"
            }
            print("Booking successful:", response_data)
            return jsonify(response_data), 201
            
        except Exception as e:
            print(f"Booking error: {str(e)}")
            return jsonify({"error": "An error occurred while processing your booking"}), 500

    @app.route('/bookings', methods=['GET'])
    @jwt_required() # Assuming /bookings should also be protected
    def get_bookings():
        current_user = get_jwt_identity() # Assuming bookings are fetched for the logged-in user
        # email = request.args.get("email") # This would allow fetching any user's bookings if not restricted
        user_bookings = bookings.find({"user_email": current_user})
        return jsonify([format_booking(b) for b in user_bookings])
    
    @app.route('/contact', methods=['POST'])
    def contact_us():
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            # Validate required fields
            required_fields = ['name', 'email', 'phone', 'message']
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
            
            # Create contact document
            contact = {
                "name": data["name"],
                "email": data["email"],
                "phone": data["phone"],
                "message": data["message"],
                "received_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Get contact collection
            contacts = mongo.db.contacts
            
            # Insert into database
            result = contacts.insert_one(contact)
            
            response = {
                "message": "Your inquiry has been received! We'll get back to you soon.",
                "contact_id": str(result.inserted_id)
            }
            return jsonify(response), 201
        
        except Exception as e:
            print(f"Contact form error: {str(e)}")
            return jsonify({"error": "An error occurred while processing your inquiry"}), 500


    @app.route('/profile', methods=['GET'])
    @jwt_required()
    def get_profile():
        current_user = get_jwt_identity()
        user = mongo.db.users.find_one({"email": current_user})
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify({
            "email": user["email"],  # Email is guaranteed to exist
            "name": user.get("name", ""),  # Use get() with default values
            "phone": user.get("phone", ""),
            "address": user.get("address", "")
        }), 200

    @app.route('/profile', methods=['PUT'])
    @jwt_required()
    def update_profile():
        current_user = get_jwt_identity()
        data = request.get_json()
        
        # Only update fields that are provided
        update_data = {}
        if "name" in data:
            update_data["name"] = data["name"]
        if "phone" in data:
            update_data["phone"] = data["phone"]
        if "address" in data:
            update_data["address"] = data["address"]
            
        if update_data:
            mongo.db.users.update_one(
                {"email": current_user},
                {"$set": update_data}
            )
            
        # Return updated profile
        user = mongo.db.users.find_one({"email": current_user})
        return jsonify({
            "email": user["email"],
            "name": user.get("name", ""),
            "phone": user.get("phone", ""),
            "address": user.get("address", "")
        }), 200


