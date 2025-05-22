from .schemas import mechanic_schema, mechanics_schema
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select
from app.models import Mechanic, db
from sqlalchemy.exc import IntegrityError
from . import mechanics_bp
from app.extensions import limiter, cache

#create mechanic
@mechanics_bp.route('/', methods=['POST'])
@limiter.limit("5 per day") #no more than 5 new accounts per ip address
def create_mechanic():
    try:
        input_data = request.get_json()
        if input_data is None:
            return jsonify({"error": "No input data provided"}), 400
        # Check if email already exists
        query = select(Mechanic).where(Mechanic.email == input_data.get('email'))
        existing_mechanic = db.session.execute(query).scalars().first()
        if existing_mechanic:
            return jsonify({"error": "Email already exists."}), 400

        # Validate and load data using schema
        new_mechanic = mechanic_schema.load(input_data)
        db.session.add(new_mechanic)
        db.session.commit()
        return mechanic_schema.jsonify(new_mechanic), 201

    except ValidationError as err:
        return jsonify(err.messages), 400
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": str(e)}), 500

#get all mechanics
@mechanics_bp.route('/', methods=['GET'])
@cache.cached(timeout=60) #store memchanics for 60s. does not need frequent updates
def get_mechanics():
    query = select(Mechanic)
    mechanics = db.session.execute(query).scalars().all()
    return mechanics_schema.jsonify(mechanics)

#get mechanic by id
@mechanics_bp.route('/<int:id>', methods=['GET'])
@cache.cached(timeout=60) #store memchanic for 60s. does not need frequent updates
def get_mechanic(id):
    mechanic = db.session.get(Mechanic, id)
    if mechanic:
        return mechanic_schema.jsonify(mechanic)
    return jsonify({"error": "Mechanic not found"}), 404

#update mechanic by id
@mechanics_bp.route('/<int:id>', methods=['PUT'])
@limiter.limit("5 per day") #prevent changes to accounts too often
def update_mechanic(id, user_id):
    mechanic = db.session.get(Mechanic, id)
    if not mechanic:
        return jsonify({"error": "Mechanic not found"}), 404
    
    try:
        input_data = request.get_json()
        if not input_data:
            return jsonify({"error": "No input data provided"}), 400
        
        #only allow these fields to be updated
        allowed_fields = ['name', 'email', 'phone', 'salary']
        for key in allowed_fields:
            if key in input_data:
                setattr(mechanic, key, input_data[key])

        db.session.commit()
        return mechanic_schema.jsonify(mechanic)

    except ValidationError as err:
        return jsonify(err.messages), 400

    except IntegrityError:
        #rollback if email already exists
        db.session.rollback()
        return jsonify({"error": "Email already exists."}), 400

    except Exception as e:
        db.session.rollback()
        print(f"Unexpected error during update: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

#delete mechanic
@mechanics_bp.route('/<int:id>', methods=['DELETE'])
@limiter.limit("5 per day") #limit the amount of accounts deleted to 5 max
def delete_mechanic(id, user_id):
    mechanic = db.session.get(Mechanic, id)
    if not mechanic:
        return jsonify({"error": "Mechanic not found"}), 404

    db.session.delete(mechanic)
    db.session.commit()
    return jsonify({"message": f"Mechanic {id} deleted"}), 200
