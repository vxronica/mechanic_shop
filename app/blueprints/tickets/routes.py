from .schemas import ticket_schema, tickets_schema
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select
from app.models import ServiceTicket, Customer, Mechanic, db, Inventory
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
        
        # update only fields that are provided
        if 'VIN' in input_data:
            ticket.VIN = input_data['VIN']

        if 'service_date' in input_data:
            try:
                ticket.service_date = datetime.strptime(input_data['service_date'], "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

        if 'service_desc' in input_data:
            ticket.service_desc = input_data['service_desc']

        if 'customer_id' in input_data:
            customer = db.session.get(Customer, input_data['customer_id'])
            if not customer:
                return jsonify({"error": "Invalid customer ID"}), 400
            ticket.customer_id = input_data['customer_id']

        if 'mechanic_ids' in input_data:
            mechanics = db.session.query(Mechanic).filter(Mechanic.id.in_(input_data['mechanic_ids'])).all()
            if not mechanics or len(mechanics) != len(input_data['mechanic_ids']):
                return jsonify({"error": "Invalid mechanic IDs"}), 400
            ticket.mechanics = mechanics

        db.session.commit()
        return ticket_schema.jsonify(ticket), 200

    except ValidationError as err:
        return jsonify(err.messages), 400
    except Exception as e:
        db.session.rollback()
        print(f"Unexpected error during ticket update: {e}")
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

#edit mechanics
@tickets_bp.route('/<int:ticket_id>/edit', methods=['PUT'])
def update_ticket_mechanics(ticket_id):
    ticket = db.session.get(ServiceTicket, ticket_id)
    if not ticket:
        return jsonify({"error": "Service ticket not found."}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided."}), 400

    add_ids = data.get("add_ids", [])
    remove_ids = data.get("remove_ids", [])

    try:
        # add mechanics
        for mech_id in add_ids:
            mechanic = db.session.get(Mechanic, mech_id)
            if mechanic and mechanic not in ticket.mechanics:
                ticket.mechanics.append(mechanic)

        # remove mechanics
        for mech_id in remove_ids:
            mechanic = db.session.get(Mechanic, mech_id)
            if mechanic and mechanic in ticket.mechanics:
                ticket.mechanics.remove(mechanic)

        db.session.commit()
        return jsonify({"message": "Ticket mechanics updated successfully."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

#add part to service ticket
@tickets_bp.route('/<int:ticket_id>/add_part', methods=['PUT'])
def add_part_to_ticket(ticket_id):
    ticket = db.session.get(ServiceTicket, ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON data"}), 400

    part_id = data.get('part_id')
    if not part_id:
        return jsonify({"error": "Missing part_id"}), 400

    part = db.session.get(Inventory, part_id)
    if not part:
        return jsonify({"error": "Part not found"}), 404

    if part in ticket.parts:
        return jsonify({"message": "Part already associated with this ticket."}), 200

    try:
        ticket.parts.append(part)
        db.session.commit()
        return jsonify({"message": f"Part {part.name} added to ticket {ticket_id}"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to add part to ticket", "details": str(e)}), 500
