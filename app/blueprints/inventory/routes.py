from flask import request, jsonify
from . import inventory_bp
from .schemas import inventory_schema, inventories_schema
from app.models import Inventory, db
from sqlalchemy import select
from marshmallow import ValidationError

# Create a part in inventory
@inventory_bp.route("/", methods=["POST"])
def create_part():
    try:
        part_data = inventory_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    db.session.add(part_data)
    db.session.commit()

    return inventory_schema.jsonify(part_data), 201

# Get all parts
@inventory_bp.route("/", methods=["GET"])
def get_parts():
    query = select(Inventory)
    result = db.session.execute(query).scalars().all()
    return inventories_schema.jsonify(result), 200

# Get a single part
@inventory_bp.route("/<int:part_id>", methods=["GET"])
def get_part(part_id):
    query = select(Inventory).where(Inventory.id == part_id)
    part = db.session.execute(query).scalars().first()

    if part is None:
        return jsonify({"message": "Invalid part ID"}), 404

    return inventory_schema.jsonify(part), 200

#update part
@inventory_bp.route("/<int:part_id>", methods=["PUT"])
def update_part(part_id):
    part = db.session.get(Inventory, part_id)
    if part is None:
        return jsonify({"message": "Invalid part ID"}), 404

    if not request.json:
        return jsonify({"message": "Missing JSON in request"}), 400

    try:
        #load and validate JSON data
        part_data = inventory_schema.load(request.json, partial=True) #partial=True allows partial updates
    except ValidationError as e:
        return jsonify(e.messages), 400

    # update part
    for field in request.json.keys():
        setattr(part, field, getattr(part_data, field))

    db.session.commit()
    return inventory_schema.jsonify(part), 200

# delete a part
@inventory_bp.route("/<int:part_id>", methods=["DELETE"])
def delete_part(part_id):
    query = select(Inventory).where(Inventory.id == part_id)
    part = db.session.execute(query).scalars().first()

    if part is None:
        return jsonify({"message": "Invalid part ID"}), 404

    db.session.delete(part)
    db.session.commit()
    return jsonify({"message": f"Successfully deleted part {part_id}"}), 200