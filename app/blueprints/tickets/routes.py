from .schemas import ticket_schema, tickets_schema
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select
from app.models import ServiceTicket, Customer, Mechanic, db
from . import tickets_bp
from datetime import datetime
from app.extensions import limiter, cache

#create ticket
@tickets_bp.route('/', methods=['POST'])
@limiter.limit("100 per day") #a small mechanic company likely will not have more than 100 issues in a day. 100 tix max
def create_ticket():
    try:
        input_data = request.get_json()
        if input_data is None:
            return jsonify({"error": "No input data provided"}), 400
        
        # Check for required fields
        required_fields = ['VIN', 'service_date', 'service_desc', 'customer_id', 'mechanic_ids']
        missing_fields = [field for field in required_fields if field not in input_data]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
        
        # validate customer ID
        customer = db.session.get(Customer, input_data.get('customer_id'))
        if not customer:
            return jsonify({"error": "Invalid customer ID"}), 400

        #validate mechanic IDs
        mechanics = db.session.query(Mechanic).filter(Mechanic.id.in_(input_data.get('mechanic_ids', []))).all()
        if not mechanics or len(mechanics) != len(input_data.get('mechanic_ids', [])):
            return jsonify({"error": "Invalid mechanic IDs"}), 400

        #convert service_date from string to date object
        service_date = datetime.strptime(input_data['service_date'], "%Y-%m-%d").date()

        # Create ticket instance
        new_ticket = ServiceTicket(
            VIN=input_data['VIN'],
            service_date=service_date,
            service_desc=input_data['service_desc'],
            customer_id=input_data['customer_id'],
            mechanics=mechanics
        )

        db.session.add(new_ticket)
        db.session.commit()
        return ticket_schema.jsonify(new_ticket), 201

    except ValidationError as err:
        return jsonify(err.messages), 400
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": str(e)}), 500

#get all service tickets
@tickets_bp.route('/', methods=['GET'])
@cache.cached(timeout=60) #store tickets accessed for 60s. tickets are not frequently updated
def get_tickets():
    tickets = db.session.execute(select(ServiceTicket)).scalars().all()
    return tickets_schema.jsonify(tickets)

#get tickets by id
@tickets_bp.route('/<int:id>', methods=['GET'])
@cache.cached(timeout=60) #store tickets accessed for 60s. tickets are not frequently updated
def get_ticket(id):
    ticket = db.session.get(ServiceTicket, id)
    if ticket:
        return ticket_schema.jsonify(ticket)
    return jsonify({"error": "Ticket not found"}), 404

#update ticket by id
@tickets_bp.route('/<int:id>', methods=['PUT'])
@limiter.limit("100 per day") ##a small mechanic company likely will not have more than 100 issues in a day. 100 tix max
def update_ticket(id):
    ticket = db.session.get(ServiceTicket, id)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404

    try:
        input_data = request.get_json()
        if not input_data:
            return jsonify({"error": "No input data provided"}), 400

        # validate customer ID
        customer = db.session.get(Customer, input_data.get('customer_id'))
        if not customer:
            return jsonify({"error": "Invalid customer ID"}), 400

        #validate mechanic IDs
        mechanics = db.session.query(Mechanic).filter(Mechanic.id.in_(input_data.get('mechanic_ids', []))).all()
        if not mechanics or len(mechanics) != len(input_data.get('mechanic_ids', [])):
            return jsonify({"error": "Invalid mechanic IDs"}), 400

        #update ticket fields
        ticket.VIN = input_data['VIN']
        ticket.service_date = datetime.strptime(input_data['service_date'], "%Y-%m-%d").date()
        ticket.service_desc = input_data['service_desc']
        ticket.customer_id = input_data['customer_id']
        ticket.mechanics = mechanics

        db.session.commit()
        return ticket_schema.jsonify(ticket)

    except ValidationError as err:
        return jsonify(err.messages), 400
    except Exception as e:
        db.session.rollback()
        print(f"Unexpected error during ticket update: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

# @tickets_bp.route('/<int:id>', methods=['DELETE'])
# def delete_ticket(id):
#     ticket = db.session.get(ServiceTicket, id)
#     if not ticket:
#         return jsonify({"error": "Ticket not found"}), 404

#     db.session.delete(ticket)
#     db.session.commit()
#     return jsonify({"message": f"Service ticket {id} deleted"}), 200