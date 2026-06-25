import pytest
import uuid
from server import app, bcrypt


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

class TestSignUp():
    def test_integration_signup_success(self, client):
        #Arrange 
        unique_email = f"integration_user_{uuid.uuid4().hex[:6]}@test.com"
        signup_data = {
            "name" : "Integration User",
            "email" : unique_email, 
            "password": "Password123!"
        }

        #Act 
        response = client.post('/api/signup', json=signup_data)

        #Assert
        assert response.status_code == 201
        assert b"User registered successfully!" in response.data

    def test_integration_signup_failed_duplicate_email(self, client):
        #Arrange 
        duplicate_email = f"integration_duplicate_{uuid.uuid4().hex[:6]}@test.com"

        signup_first = {
            "name" : "first",
            "email" : duplicate_email, 
            "password" : "pass123"
        }

        signup_second = {
            "name" : "second", 
            "email" : duplicate_email, 
            "password" : "pass1234"
        }

        #Act 
        response_first = client.post('/api/signup', json=signup_first)
        response_second = client.post('/api/signup', json=signup_second)

        #Assert 
        assert response_first.status_code == 201 
        assert response_second.status_code == 400

        assert b"Email already exists" in response_second.data

class TestLogin():
    def test_integration_login_succeed(self, client):
        #Arrange 
        #signup first to ensure user exists
        unique_email = f"integration_login_user_{uuid.uuid4().hex[:6]}@test.com"
        signup_data = {
            "name" : "Integration Login User",
            "email" : unique_email,
            "password": "Password123!"
        }

        client.post('/api/signup', json=signup_data)


        #take the same email and password to login
        login_data = {
            "email" : unique_email,
            "password" : "Password123!"
        }   

        #Act
        response = client.post('/api/login', json=login_data)

        #Assert
        assert response.status_code == 200
        assert b"Login successful" in response.data

    def test_integration_login_failed_wrong_password(self, client):
        #Arrange 
        #signup first to ensure user exists
        unique_email = f"integration_wrong_pass_user_{uuid.uuid4().hex[:6]}@test.com"
        signup_data = {
            "name" : "Integration Wrong Pass User",
            "email" : unique_email,
            "password": "Password123!"
        }

        client.post('/api/signup', json=signup_data)

        #take the same email but wrong password to login
        login_data = {
            "email" : unique_email,
            "password" : "WrongPassword!"
        }   

        #Act
        response = client.post('/api/login', json=login_data)

        #Assert
        assert response.status_code == 401
        assert b"Invalid email or password" in response.data

    def test_integration_login_failed_nonexistent_email(self, client):
        #Arrange
        login_data = {
            "email" : "nonexistent@test.com",
            "password" : "Password123!"
        }

        #Act
        response = client.post('/api/login', json=login_data)

        #Assert
        assert response.status_code == 401
        assert b"Invalid email or password" in response.data


class TestMe:
    def test_integration_me_after_login(self, client):
        #Arrange - sign up and log in
        unique_email = f"me_user_{uuid.uuid4().hex[:6]}@test.com"
        client.post('/api/signup', json={"name": "Me User", "email": unique_email, "password": "Password123!"})
        client.post('/api/login', json={"email": unique_email, "password": "Password123!"})

        #Act
        response = client.get('/api/me')

        #Assert
        assert response.status_code == 200
        assert b"Me User" in response.data

    def test_integration_me_unauthorized(self, client):
        #Act
        response = client.get('/api/me')

        #Assert
        assert response.status_code == 401


class TestUpdateBio:
    def test_integration_update_bio(self, client):
        #Arrange - sign up and log in
        unique_email = f"bio_user_{uuid.uuid4().hex[:6]}@test.com"
        client.post('/api/signup', json={"name": "Bio User", "email": unique_email, "password": "Password123!"})
        client.post('/api/login', json={"email": unique_email, "password": "Password123!"})

        #Act
        response = client.put('/api/me/bio', json={"bio": "My integration bio"})

        #Assert
        assert response.status_code == 200
        assert b"Bio updated successfully" in response.data

    def test_integration_update_bio_unauthorized(self, client):
        #Act
        response = client.put('/api/me/bio', json={"bio": "Bio"})

        #Assert
        assert response.status_code == 401


class TestFeed:
    def test_integration_feed_returns_list(self, client):
        #Act
        response = client.get('/api/feed')

        #Assert
        assert response.status_code == 200

    def test_integration_feed_with_pagination(self, client):
        #Act
        response = client.get('/api/feed?limit=5&offset=0')

        #Assert
        assert response.status_code == 200


class TestNewPost:
    def test_integration_create_post(self, client):
        #Arrange - sign up and log in
        unique_email = f"post_user_{uuid.uuid4().hex[:6]}@test.com"
        client.post('/api/signup', json={"name": "Post User", "email": unique_email, "password": "Password123!"})
        client.post('/api/login', json={"email": unique_email, "password": "Password123!"})

        data = {"title": "Integration Post", "body": "Integration post body", "image_url": ""}

        #Act
        response = client.post('/api/new-post', json=data)

        #Assert
        assert response.status_code == 201
        assert b"Post created successfully" in response.data

    def test_integration_create_post_unauthorized(self, client):
        #Act
        response = client.post('/api/new-post', json={"title": "Test", "body": "Body", "image_url": ""})

        #Assert
        assert response.status_code == 401


class TestUsers:
    def test_integration_get_all_users(self, client):
        #Act
        response = client.get('/api/users')

        #Assert
        assert response.status_code == 200


class TestSearch:
    def test_integration_search_finds_user(self, client):
        #Arrange - create a user with a unique name to search for
        unique_name = f"SearchUser{uuid.uuid4().hex[:6]}"
        unique_email = f"search_{uuid.uuid4().hex[:6]}@test.com"
        client.post('/api/signup', json={"name": unique_name, "email": unique_email, "password": "Password123!"})

        #Act
        response = client.get(f'/api/users/search?q={unique_name}')

        #Assert
        assert response.status_code == 200
        assert unique_name.encode() in response.data

    def test_integration_search_empty_query(self, client):
        #Act
        response = client.get('/api/users/search')

        #Assert
        assert response.status_code == 200


class TestFollow:
    def test_integration_follow_and_unfollow(self, client):
        #Arrange - create two users
        email_1 = f"follower_{uuid.uuid4().hex[:6]}@test.com"
        email_2 = f"followed_{uuid.uuid4().hex[:6]}@test.com"

        client.post('/api/signup', json={"name": "Follower", "email": email_1, "password": "Password123!"})
        client.post('/api/signup', json={"name": "Followed", "email": email_2, "password": "Password123!"})

        # Log in as user 2 to get their ID
        client.post('/api/login', json={"email": email_2, "password": "Password123!"})
        user_2_id = client.get('/api/me').get_json()['id']

        # Log in as user 1
        client.post('/api/login', json={"email": email_1, "password": "Password123!"})

        #Act - follow user 2
        follow_response = client.post(f'/api/users/{user_2_id}/follow')

        #Assert
        assert follow_response.status_code == 200
        assert b"Successfully followed user" in follow_response.data

        #Act - unfollow user 2
        unfollow_response = client.post(f'/api/users/{user_2_id}/unfollow')

        #Assert
        assert unfollow_response.status_code == 200
        assert b"Successfully unfollowed user" in unfollow_response.data

    def test_integration_get_followers(self, client):
        #Arrange - create a user to check followers of
        unique_email = f"profile_user_{uuid.uuid4().hex[:6]}@test.com"
        client.post('/api/signup', json={"name": "Profile User", "email": unique_email, "password": "Password123!"})
        client.post('/api/login', json={"email": unique_email, "password": "Password123!"})
        user_id = client.get('/api/me').get_json()['id']

        #Act
        response = client.get(f'/api/users/{user_id}/followers')

        #Assert
        assert response.status_code == 200

    def test_integration_get_following(self, client):
        #Arrange
        unique_email = f"following_user_{uuid.uuid4().hex[:6]}@test.com"
        client.post('/api/signup', json={"name": "Following User", "email": unique_email, "password": "Password123!"})
        client.post('/api/login', json={"email": unique_email, "password": "Password123!"})
        user_id = client.get('/api/me').get_json()['id']

        #Act
        response = client.get(f'/api/users/{user_id}/following')

        #Assert
        assert response.status_code == 200


class TestUserProfile:
    def test_integration_get_user_profile(self, client):
        #Arrange
        unique_email = f"profile_{uuid.uuid4().hex[:6]}@test.com"
        client.post('/api/signup', json={"name": "Profile Test", "email": unique_email, "password": "Password123!"})
        client.post('/api/login', json={"email": unique_email, "password": "Password123!"})
        user_id = client.get('/api/me').get_json()['id']

        #Act
        response = client.get(f'/api/users/{user_id}/profile')

        #Assert
        assert response.status_code == 200
        assert b"Profile Test" in response.data

    def test_integration_get_user_profile_not_found(self, client):
        #Act
        response = client.get('/api/users/999999/profile')

        #Assert
        assert response.status_code == 404


class TestFeedFollowing:
    def test_integration_feed_following_authorized(self, client):
        #Arrange - sign up and log in
        unique_email = f"feed_user_{uuid.uuid4().hex[:6]}@test.com"
        client.post('/api/signup', json={"name": "Feed User", "email": unique_email, "password": "Password123!"})
        client.post('/api/login', json={"email": unique_email, "password": "Password123!"})

        #Act
        response = client.get('/api/feed/following')

        #Assert
        assert response.status_code == 200

    def test_integration_feed_following_unauthorized(self, client):
        #Act
        response = client.get('/api/feed/following')

        #Assert
        assert response.status_code == 401




