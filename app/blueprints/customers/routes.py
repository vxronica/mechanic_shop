from .schemas import customer_schema, customers_schema
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select
from app.models import Customer, db
from sqlalchemy.exc import IntegrityError
from . import customers_bp

# CREATE customer
@customers_bp.route('/', methods=['POST'])
def create_customer():
    try:
        input_data = request.get_json()
        if input_data is None:
            return jsonify({"error": "No input data provided"}), 400

        # Check for duplicate email first
        query = select(Customer).where(Customer.email == input_data.get('email'))
        existing_customer = db.session.execute(query).scalars().first()
        if existing_customer:
            return jsonify({"error": "Email already exists."}), 400

        # This returns a Customer instance because load_instance=True
        new_customer = customer_schema.load(input_data)
        db.session.add(new_customer)
        db.session.commit()
        return customer_schema.jsonify(new_customer), 201

    except ValidationError as err:
        return jsonify(err.messages), 400
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": str(e)}), 500

# Get all customers
@customers_bp.route('/', methods=['GET'])
def get_customers():
    query = select(Customer)
    customers = db.session.execute(query).scalars().all()
    return customers_schema.jsonify(customers)

# Get customer by id
@customers_bp.route('/<int:id>', methods=['GET'])
def get_customer(id):
    customer = db.session.get(Customer, id)
    if customer:
        return customer_schema.jsonify(customer)
    return jsonify({"error": "Customer not found"}), 404

# UPDATE customer
@customers_bp.route('/<int:id>', methods=['PUT'])
def update_customer(id):
    customer = db.session.get(Customer, id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    
    try:
        input_data = request.get_json()
        if not input_data:
            return jsonify({"error": "No input data provided"}), 400

        # Validate only known fields
        allowed_fields = ['name', 'email', 'phone']
        for key in allowed_fields:
            if key in input_data:
                setattr(customer, key, input_data[key])

        db.session.commit()
        return customer_schema.jsonify(customer)

    except ValidationError as err:
        return jsonify(err.messages), 400

    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": "Email already exists."}), 400

    except Exception as e:
        db.session.rollback()
        print(f"Unexpected error during update: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

# DELETE customer
@customers_bp.route('/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer = db.session.get(Customer, id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": f"Customer {id} deleted"}), 200