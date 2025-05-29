import unittest
from app import create_app, db

class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_part(self):
        res = self.client.post('/inventory/', json={"name": "Air Filter", "price": 19.99})
        self.assertEqual(res.status_code, 201)
        self.assertIn("id", res.get_json())

    def test_create_part_missing_field(self):
        res = self.client.post('/inventory/', json={"price": 5})
        self.assertEqual(res.status_code, 400)

    def test_get_parts(self):
        self.client.post('/inventory/', json={"name": "Window", "price": 15.00})
        res = self.client.get('/inventory/')
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.get_json(), list)

    def test_get_part_by_id(self):
        res = self.client.post('/inventory/', json={"name": "Brake Pad", "price": 30.00})
        part_id = res.get_json()['id']
        get_res = self.client.get(f'/inventory/{part_id}')
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.get_json()["id"], part_id)

    def test_update_part(self):
        res = self.client.post('/inventory/', json={"name": "Radiator", "price": 100.00})
        part_id = res.get_json()['id']
        update = self.client.put(f'/inventory/{part_id}', json={"price": 120.00})
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.get_json()["price"], 120.00)

    def test_delete_part(self):
        res = self.client.post('/inventory/', json={"name": "Tire", "price": 50.00})
        part_id = res.get_json()['id']
        delete = self.client.delete(f'/inventory/{part_id}')
        self.assertEqual(delete.status_code, 200)
        # Verify it's actually deleted
        res_check = self.client.get(f'/inventory/{part_id}')
        self.assertEqual(res_check.status_code, 404)

if __name__ == '__main__':
    unittest.main()