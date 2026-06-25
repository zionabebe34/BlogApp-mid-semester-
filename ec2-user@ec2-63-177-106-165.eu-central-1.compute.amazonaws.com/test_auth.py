import pytest
import bcrypt
import sys
from unittest.mock import MagicMock, patch

sys.modules.pop('server', None)
with patch('mysql.connector.pooling.MySQLConnectionPool'):
    from server import app




@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


class TestPasswordHashing:
    def test_password_hashing_generates_hash(self):
        #Arrange
        password = "my_secure_password"

        #Act
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        #Assert
        assert hashed_password != password.encode('utf-8')
        assert bcrypt.checkpw(password.encode('utf-8'), hashed_password)

    def test_password_verification_success(self):
        #Arrange
        password = "my_secure_password"
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        #Act
        is_valid = bcrypt.checkpw(password.encode('utf-8'), hashed_password)

        #Assert
        assert is_valid is True

    def test_password_verification_failure(self, client):
        #Arrange
        password = "my_secure_password"
        wrong_password = "wrong_password"
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        #Act
        is_valid = bcrypt.checkpw(wrong_password.encode('utf-8'), hashed_password)

        #Assert
        assert is_valid is False


class TestSignup:
    def test_signup_route(self, client):
        #Arrange
        mock_cursor = MagicMock()
        mock_db = MagicMock()
        mock_db.cursor.return_value = mock_cursor

        data = {
            "name": "testuser",
            "email": "testuser@example.com",
            "password": "testpassword"
        }

        #Act
        with patch('server.get_db', return_value=mock_db):
            response = client.post('/api/signup', json=data)

        #Assert
        assert response.status_code == 201
        assert b"User registered successfully" in response.data


class TestLogin:
    def test_login_route(self, client):
        #Arrange
        password = "testpassword"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Fake user row: (id, name, email, password)
        fake_user = (1, "testuser", "testuser@example.com", hashed)

        mock_cursor = MagicMock()
        mock_db = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = fake_user

        login_data = {
            "email": "testuser@example.com",
            "password": "testpassword"
        }

        #Act
        with patch('server.get_db', return_value=mock_db):
            response = client.post('/api/login', json=login_data)

        #Assert
        assert response.status_code == 200
        assert b"Login successful" in response.data

class TestLogout:
    def test_logout_route(self, client):
        #Arrange - Mock
        mock_cursor = MagicMock()
        mock_db = MagicMock()
        mock_db.cursor.return_value = mock_cursor

        client.set_cookie('session_id', 'fake-session-id-123')

        #Act
        with patch('server.get_db', return_value=mock_db):
            response = client.post('/api/logout')

        #Assert
        assert response.status_code == 200
        assert b"Logout successful" in response.data


class TestMe:
    def test_me_authorized(self, client):
        #Arrange
        fake_user = (1, "testuser", "testuser@example.com")
        mock_cursor = MagicMock()
        mock_db = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = fake_user
        client.set_cookie('session_id', 'fake-session-id')

        #Act
        with patch('server.get_db', return_value=mock_db):
            response = client.get('/api/me')

        #Assert
        assert response.status_code == 200
        assert b"testuser" in response.data

    def test_me_unauthorized(self, client):
        #Arrange - no cookie set

        #Act
        response = client.get('/api/me')

        #Assert
        assert response.status_code == 401


class TestUpdateBio:
    def test_update_bio_authorized(self, client):
        #Arrange
        mock_cursor = MagicMock()
        mock_db = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)
        client.set_cookie('session_id', 'fake-session-id')

        #Act
        with patch('server.get_db', return_value=mock_db):
            response = client.put('/api/me/bio', json={"bio": "My new bio"})

        #Assert
        assert response.status_code == 200
        assert b"Bio updated successfully" in response.data

    def test_update_bio_unauthorized(self, client):
        #Arrange - no cookie

        #Act
        response = client.put('/api/me/bio', json={"bio": "My new bio"})

        #Assert
        assert response.status_code == 401


class TestFeed:
    def test_feed_returns_posts(self, client):
        #Arrange
        mock_cursor = MagicMock()
        mock_db = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        #Act
        with patch('server.get_db', return_value=mock_db):
            response = client.get('/api/feed')

        #Assert
        assert response.status_code == 200


class TestNewPost:
    def test_new_post_authorized(self, client):
        #Arrange
        mock_cursor = MagicMock()
        mock_db = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)
        client.set_cookie('session_id', 'fake-session-id')

        data = {"title": "Test Post", "body": "Test body", "image_url": ""}

        #Act
        with patch('server.get_db', return_value=mock_db):
            response = client.post('/api/new-post', json=data)

        #Assert
        assert response.status_code == 201
        assert b"Post created successfully" in response.data

    def test_new_post_unauthorized(self, client):
        #Arrange
        data = {"title": "Test Post", "body": "Test body", "image_url": ""}

        #Act
        response = client.post('/api/new-post', json=data)

        #Assert
        assert response.status_code == 401


class TestUsers:
    def test_get_all_users(self, client):
        #Arrange
        mock_cursor = MagicMock()
        mock_db = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [(1, "testuser", "testuser@example.com", 2)]

        #Act
        with patch('server.get_db', return_value=mock_db):
            response = client.get('/api/users')

        #Assert
        assert response.status_code == 200
        assert b"testuser" in response.data


class TestUserPosts:
    def test_get_user_posts(self, client):
        #Arrange
        mock_cursor = MagicMock()
        mock_db = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ("testuser",)
        mock_cursor.fetchall.return_value = [(1, "My Post", "Post body")]

        #Act
        with patch('server.get_db', return_value=mock_db):
            response = client.get('/api/user-posts/1')

        #Assert
        assert response.status_code == 200
        assert b"testuser" in response.data


class TestUserProfile:
    def test_get_user_profile_found(self, client):
        #Arrange
        mock_cursor = MagicMock()
        mock_db = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        mock_cursor.fetchone.side_effect = [
            {'id': 1, 'name': 'testuser', 'email': 'testuser@example.com', 'bio': 'Hello!', 'profile_picture_url': ''},
            {'count': 5},
            {'count': 3}
        ]
        mock_cursor.fetchall.return_value = []

        #Act
        with patch('server.get_db', return_value=mock_db):
            response = client.get('/api/users/1/profile')

        #Assert
        assert response.status_code == 200
        assert b"testuser" in response.data

    def test_get_user_profile_not_found(self, client):
        #Arrange
        mock_cursor = MagicMock()
        mock_db = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        #Act
        with patch('server.get_db', return_value=mock_db):
            response = client.get('/api/users/999/profile')

        #Assert
        assert response.status_code == 404


class TestFollow:
    def test_follow_user(self, client):
        #Arrange
        mock_cursor = MagicMock()
        mock_db = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)
        client.set_cookie('session_id', 'fake-session-id')

        #Act
        with patch('server.get_db', return_value=mock_db):
            response = client.post('/api/users/2/follow')

        #Assert
        assert response.status_code == 200
        assert b"Successfully followed user" in response.data

    def test_follow_user_unauthorized(self, client):
        #Act
        response = client.post('/api/users/2/follow')

        #Assert
        assert response.status_code == 401

    def test_follow_self_returns_400(self, client):
        #Arrange - logged-in user id=1, trying to follow user id=1
        mock_cursor = MagicMock()
        mock_db = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)
        client.set_cookie('session_id', 'fake-session-id')

        #Act
        with patch('server.get_db', return_value=mock_db):
            response = client.post('/api/users/1/follow')

        #Assert
        assert response.status_code == 400
        assert b"You cannot follow yourself" in response.data

    def test_unfollow_user(self, client):
        #Arrange
        mock_cursor = MagicMock()
        mock_db = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)
        client.set_cookie('session_id', 'fake-session-id')

        #Act
        with patch('server.get_db', return_value=mock_db):
            response = client.post('/api/users/2/unfollow')

        #Assert
        assert response.status_code == 200
        assert b"Successfully unfollowed user" in response.data

    def test_get_followers(self, client):
        #Arrange
        mock_cursor = MagicMock()
        mock_db = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [{'id': 2, 'name': 'follower', 'email': 'f@example.com', 'profile_picture_url': ''}]

        #Act
        with patch('server.get_db', return_value=mock_db):
            response = client.get('/api/users/1/followers')

        #Assert
        assert response.status_code == 200

    def test_get_following(self, client):
        #Arrange
        mock_cursor = MagicMock()
        mock_db = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        #Act
        with patch('server.get_db', return_value=mock_db):
            response = client.get('/api/users/1/following')

        #Assert
        assert response.status_code == 200


class TestSearch:
    def test_search_users(self, client):
        #Arrange
        mock_cursor = MagicMock()
        mock_db = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [{'id': 1, 'name': 'testuser', 'email': 'testuser@example.com', 'profile_picture_url': ''}]

        #Act
        with patch('server.get_db', return_value=mock_db):
            response = client.get('/api/users/search?q=testuser')

        #Assert
        assert response.status_code == 200
        assert b"testuser" in response.data

    def test_search_empty_query(self, client):
        #Act
        response = client.get('/api/users/search')

        #Assert
        assert response.status_code == 200


class TestFeedFollowing:
    def test_feed_following_authorized(self, client):
        #Arrange
        mock_cursor = MagicMock()
        mock_db = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {'user_id': 1}
        mock_cursor.fetchall.return_value = []
        client.set_cookie('session_id', 'fake-session-id')

        #Act
        with patch('server.get_db', return_value=mock_db):
            response = client.get('/api/feed/following')

        #Assert
        assert response.status_code == 200

    def test_feed_following_unauthorized(self, client):
        #Act
        response = client.get('/api/feed/following')

        #Assert
        assert response.status_code == 401



