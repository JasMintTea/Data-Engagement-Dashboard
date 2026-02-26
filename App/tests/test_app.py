import os, tempfile, pytest, logging, unittest
from werkzeug.security import check_password_hash, generate_password_hash

from App.main import create_app
from App.database import db, create_db
from App.models import User
from App.controllers import (
    create_user,
    get_all_users_json,
    login,
    get_user,
    update_user
)


LOGGER = logging.getLogger(__name__)

'''
   Unit Tests
'''
class UserUnitTests(unittest.TestCase):

    def test_new_user(self):
        user = User(firstname="Bob", lastname="Smith", username="bob", email="bob@test.com", password="bobpass")
        assert user.username == "bob"
        assert user.email == "bob@test.com"

    # pure function no side effects or integrations called
    def test_get_json(self):
        user = User(firstname="Bob", lastname="Smith", username="bob", email="bob@test.com", password="bobpass")
        user_json = user.get_json()
        self.assertDictEqual(user_json, {"id":None, "username":"bob", "email":"bob@test.com"})
    
    def test_hashed_password(self):
        password = "mypass"
        hashed = generate_password_hash(password)
        user = User(firstname="Bob", lastname="Smith", username="bob", email="bob@test.com", password="bobpass")
        assert user.password != password

    def test_check_password(self):
        password = "mypass"
        user = User(firstname="Bob", lastname="Smith", username="bob", email="bob@test.com", password="bobpass")
        assert user.check_password(password)

'''
    Integration Tests
'''

# This fixture creates an empty database for the test and deletes it after the test
# scope="class" would execute the fixture once and resued for all methods in the class
@pytest.fixture(autouse=True, scope="module")
def empty_db():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///test.db'})
    create_db()
    yield app.test_client()
    db.drop_all()


def test_authenticate():
    user = create_user(firstname="Bob", lastname="Smith", username="bob", email="bob@test.com", password="bobpass")
    assert login("bob", "bobpass") is not None

class UsersIntegrationTests(unittest.TestCase):

    def test_create_user(self):
        user = create_user(firstname="Rick", lastname="Whales", username="rick", email="rick@test.com", password="rickpass")
        assert user.username == "rick"

    def test_get_all_users_json(self):
        users_json = get_all_users_json()
        self,self.assertIsInstance(users_json, list)
        if len(users_json) > 0:
            self.assertIn('username', users_json[0])
            self.assertIn('email', users_json[0])

    # Tests data changes in the database
    def test_update_user(self):
        user = create_user(firstname="Test", lastname="User", username="testuser", email="test@test.com", password="testpass")
        user_id = 1

        update_user(1, "ronnie")
        updated_user = get_user(1)
        assert updated_user.username == "ronnie"
        

