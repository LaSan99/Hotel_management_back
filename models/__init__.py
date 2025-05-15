from bson.objectid import ObjectId

def format_room(room):
    return {
        "_id": str(room["_id"]),
        "title": room["title"],
        "description": room["description"],
        "price": room["price"],
        "is_available": room["is_available"],
        "type": room["type"],
        "images": room.get("images", [])  # Array of image URLs with default empty array
    }

def format_booking(booking):
    return {
        "_id": str(booking["_id"]),
        "room_id": str(booking["room_id"]),
        "user_email": booking["user_email"],
        "guest_name": booking.get("guest_name", ""),
        "guest_phone": booking.get("guest_phone", ""),
        "num_guests": booking.get("num_guests", 1),
        "start_date": booking["start_date"],
        "end_date": booking["end_date"],
        "special_requests": booking.get("special_requests", ""),
        "total_price": booking.get("total_price", 0),
        "payment_method": booking.get("payment_method", "Credit Card"),
        "status": booking["status"],
        "created_at": booking.get("created_at", "")
    }
