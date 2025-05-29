import unittest
from app import create_app, db
from app.models import Customer, Mechanic, ServiceTicket
from datetime import date

class TicketTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            # Create customer and mechanic in the test database
            self.customer = Customer(name="Luke", email="luke@example.com", phone="1111111111", password="test")
            self.mechanic = Mechanic(name="Ana", email="ana@example.com", phone="2222222222", salary=40000)
            db.session.add(self.customer)
            db.session.add(self.mechanic)
            db.session.commit()
            # Store IDs for reference in tests
            self.customer_id = self.customer.id
            self.mechanic_id = self.mechanic.id

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_create_ticket(self):
        res = self.client.post('/tickets/', json={
            "VIN": "123ABC",
            "service_date": str(date.today()),
            "service_desc": "Engine fix",
            "customer_id": self.customer_id,
            "mechanic_ids": [self.mechanic_id]
        })
        self.assertEqual(res.status_code, 201)

    def test_get_tickets(self):
        res = self.client.get('/tickets/')
        self.assertEqual(res.status_code, 200)

    def test_get_ticket_by_id(self):
        res = self.client.post('/tickets/', json={
            "VIN": "XYZ123",
            "service_date": str(date.today()),
            "service_desc": "Oil change",
            "customer_id": self.customer_id,
            "mechanic_ids": [self.mechanic_id]
        })
        ticket_id = res.get_json()["id"]
        get_res = self.client.get(f"/tickets/{ticket_id}")
        self.assertEqual(get_res.status_code, 200)

    def test_update_ticket(self):
        # First create a ticket
        res = self.client.post('/tickets/', json={
            "VIN": "ABC987",
            "service_date": str(date.today()),
            "service_desc": "Brake",
            "customer_id": self.customer_id,
            "mechanic_ids": [self.mechanic_id]
        })
        ticket_id = res.get_json()["id"]

        # Then update it with full data as required by the route
        update_res = self.client.put(f"/tickets/{ticket_id}", json={
            "VIN": "UPDATED123",
            "service_date": str(date.today()),
            "service_desc": "Brake & oil",
            "customer_id": self.customer_id,
            "mechanic_ids": [self.mechanic_id]
        })
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.get_json()["service_desc"], "Brake & oil")

    def test_edit_mechanics_on_ticket(self):
        # Create a ticket
        create_res = self.client.post('/tickets/', json={
            "VIN": "MECH123",
            "service_date": str(date.today()),
            "service_desc": "Battery replacement",
            "customer_id": self.customer_id,
            "mechanic_ids": [self.mechanic_id]
        })
        self.assertEqual(create_res.status_code, 201)
        ticket_id = create_res.get_json()["id"]

        # Attempt to modify mechanics
        put_res = self.client.put(f"/tickets/{ticket_id}/edit", json={
            "add_ids": [],
            "remove_ids": []
        })
        self.assertEqual(put_res.status_code, 200)

    def test_add_part_invalid_ticket(self):
        # Try to add part to a ticket that doesn't exist
        res = self.client.put('/tickets/999/add_part', json={"part_id": 1})
        self.assertEqual(res.status_code, 404)

if __name__ == '__main__':
    unittest.main()