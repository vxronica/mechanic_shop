from app.extensions import ma
from app.models import ServiceTicket
from app.blueprints.customers.schemas import CustomerSchema
from app.blueprints.mechanics.schemas import MechanicSchema

class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ServiceTicket
        load_instance = True
    customer = ma.Nested(CustomerSchema)
    mechanics = ma.Nested(MechanicSchema, many=True)

ticket_schema = ServiceTicketSchema()
tickets_schema = ServiceTicketSchema(many=True)