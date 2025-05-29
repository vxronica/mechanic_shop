import unittest
from app import create_app, db
from app.models import Mechanic

class MechanicTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            mechanic = Mechanic(name='Jane Smith', email='jane@example.com', phone='1234567890', salary=50000)
            db.session.add(mechanic)
            db.session.commit()
            self.mechanic_id = mechanic.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_get_mechanics(self):
        response = self.client.get('/mechanics/')
        self.assertEqual(response.status_code, 200)

    def test_get_mechanic_by_id(self):
        response = self.client.get(f'/mechanics/{self.mechanic_id}')
        self.assertEqual(response.status_code, 200)

    def test_create_mechanic(self):
        data = {
            'name': 'Alice Johnson',
            'email': 'alice@example.com',
            'phone': '9876543210',
            'salary': 60000
        }
        response = self.client.post('/mechanics/', json=data)
        self.assertEqual(response.status_code, 201)

    def test_create_mechanic_missing_field(self):
        data = {
            'name': 'Incomplete Mechanic'
        }
        response = self.client.post('/mechanics/', json=data)
        self.assertEqual(response.status_code, 400)

    def test_update_mechanic(self):
        update_data = {
            'name': 'Jane Updated',
            'phone': '1111111111',
            'salary': 55000
        }
        response = self.client.put(f'/mechanics/{self.mechanic_id}', json=update_data)
        self.assertIn(response.status_code, [200, 400])

    def test_delete_mechanic(self):
        response = self.client.delete(f'/mechanics/{self.mechanic_id}')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()