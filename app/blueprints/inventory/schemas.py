from app.models import Inventory
from app.extensions import ma

class InventorySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Inventory
        load_instance = True

inventory_schema = InventorySchema()
inventories_schema = InventorySchema(many=True)
