import unittest
from app import create_app, db

class CustomerTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_create_customer(self):
        payload = {
            "name": "John",
            "email": "john@example.com",
            "phone": "1234567890",
            "password": "password123"
        }
        res = self.client.post('/customers', json=payload, follow_redirects=True)
        self.assertEqual(res.status_code, 201)

    def test_create_customer_missing_email(self):
        payload = {
            "name": "John",
            "phone": "1234567890",
            "password": "password123"
        }
        res = self.client.post('/customers', json=payload, follow_redirects=True)
        self.assertEqual(res.status_code, 400)

    def test_get_customers(self):
        self.client.post('/customers', json={
            "name": "Anna",
            "email": "anna@example.com",
            "phone": "1111111111",
            "password": "password123"
        }, follow_redirects=True)
        res = self.client.get('/customers', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

    def test_get_customer_by_id(self):
        res = self.client.post('/customers', json={
            "name": "Bob",
            "email": "bob@example.com",
            "phone": "2222222222",
            "password": "password123"
        }, follow_redirects=True)
        customer_id = res.get_json()['id']
        get_res = self.client.get(f'/customers/{customer_id}', follow_redirects=True)
        self.assertEqual(get_res.status_code, 200)

    def test_get_customer_invalid_id(self):
        res = self.client.get('/customers/999', follow_redirects=True)
        self.assertEqual(res.status_code, 404)

    def test_update_customer(self):
        res = self.client.post('/customers', json={
            "name": "Mark",
            "email": "mark@example.com",
            "phone": "3333333333",
            "password": "password123"
        }, follow_redirects=True)
        customer_id = res.get_json()['id']
        update = self.client.put(f'/customers/{customer_id}', json={
            "name": "Updated Mark"
        }, headers={"Authorization": "Bearer dummy"}, follow_redirects=True)
        self.assertIn(update.status_code, [200, 400])

    def test_delete_customer(self):
        res = self.client.post('/customers', json={
            "name": "Tina",
            "email": "tina@example.com",
            "phone": "4444444444",
            "password": "password123"
        }, follow_redirects=True)
        customer_id = res.get_json()['id']
        delete_res = self.client.delete(f'/customers/{customer_id}', headers={"Authorization": "Bearer dummy"}, follow_redirects=True)
        self.assertIn(delete_res.status_code, [200, 400])

    def test_customer_login_success(self):
        create_res = self.client.post('/customers', json={
            "name": "Login Test",
            "email": "login@example.com",
            "phone": "5555555555",
            "password": "mypassword"
        }, follow_redirects=True)
        self.assertEqual(create_res.status_code, 201)
        res = self.client.post('/customers/login', json={
            "email": "login@example.com",
            "password": "mypassword"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("auth_token", res.get_json())

    def test_customer_login_invalid_password(self):
        create_res = self.client.post('/customers', json={
            "name": "Login Fail",
            "email": "fail@example.com",
            "phone": "6666666666",
            "password": "correctpw"
        }, follow_redirects=True)
        self.assertEqual(create_res.status_code, 201)
        res = self.client.post('/customers/login', json={
            "email": "fail@example.com",
            "password": "wrongpw"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 401)

    def test_customer_login_missing_fields(self):
        res = self.client.post('/customers/login', json={"email": "someone@example.com"}, follow_redirects=True)
        self.assertEqual(res.status_code, 400)

if __name__ == '__main__':
    unittest.main()