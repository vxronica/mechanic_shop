from .schemas import customer_schema, customers_schema, login_schema
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select
from app.models import Customer, db, ServiceTicket
from sqlalchemy.exc import IntegrityError
from . import customers_bp
from app.extensions import limiter, cache
from app.utils.util import encode_token, token_required
from app.blueprints.tickets.schemas import tickets_schema

@customers_bp.route("/login", methods=['POST'])
def login():
    try:
        credentials = login_schema.load(request.json)
        email = credentials['email']
        password = credentials['password']
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    query =select(Customer).where(Customer.email == email) 
    user = db.session.execute(query).scalars().first()

    if user and user.password == password: #if we have a user associated with the username, validate the password
        auth_token = encode_token(user.id)

        response = {
            "status": "success",
            "message": "Successfully Logged In",
            "auth_token": auth_token
        }
        return jsonify(response), 200
    else:
        return jsonify({'messages': "Invalid email or password"}), 401

# CREATE customer
@customers_bp.route('/', methods=['POST'])
@limiter.limit("5 per day") #no more than 5 new accounts per ip address
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
#@cache.cached(timeout=60) #store members for 60s. does not need to be the most updated
def get_customers():
    try:
        page = int(request.args.get('page'))
        per_page = int(request.args.get('per_page'))
        query = select(Customer)
        customers = db.paginate(query, page=page, per_page=per_page)
        return customers_schema.jsonify(customers), 200
    except:
        query = select(Customer)
        customers = db.session.execute(query).scalars().all()
        return customers_schema.jsonify(customers)

# Get customer by id
@customers_bp.route('/<int:id>', methods=['GET'])
@cache.cached(timeout=60) #store member for 60s. does not need to be the most updated
def get_customer(id):
    customer = db.session.get(Customer, id)
    if customer:
        return customer_schema.jsonify(customer)
    return jsonify({"error": "Customer not found"}), 404

#update by id
@customers_bp.route('/<int:id>', methods=['PUT'])
@limiter.limit("5 per day")  # prevent changes to accounts too often
@token_required
def update_customer(id, user_id):
    customer = db.session.get(Customer, id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    try:
        input_data = request.get_json()
        if not input_data:
            return jsonify({"error": "No input data provided"}), 400

        allowed_fields = ['name', 'email', 'phone']

        # Handle email update separately to check uniqueness
        if 'email' in input_data and input_data['email'] != customer.email:
            existing = db.session.execute(
                select(Customer).where(Customer.email == input_data['email'])
            ).scalars().first()
            if existing:
                return jsonify({"error": "Email already exists."}), 400
            customer.email = input_data['email']

        # Update other fields
        for key in allowed_fields:
            if key != 'email' and key in input_data:
                setattr(customer, key, input_data[key])

        db.session.commit()
        return customer_schema.jsonify(customer)

    except ValidationError as err:
        return jsonify(err.messages), 400

    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email already exists."}), 400

    except Exception as e:
        db.session.rollback()
        print(f"Unexpected error during update: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

# DELETE customer
@customers_bp.route('/<int:id>', methods=['DELETE'])
@token_required
@limiter.limit("5 per day") #limit the amount of accounts deleted to 5 max
def delete_customer(id, user_id):
    customer = db.session.get(Customer, id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": f"Customer {id} deleted"}), 200

@customers_bp.route('/my-tickets', methods=['GET'])
@token_required
def get_my_tickets(user_id):
    tickets = db.session.execute(
        select(ServiceTicket).where(ServiceTicket.customer_id == user_id)
    ).scalars().all()

    return tickets_schema.jsonify(tickets), 200
