from locust import HttpUser, task, between
from settings.settings import TestSettings

class LoadUser(HttpUser):
    wait_time = between(0, 5)
    settings = TestSettings()
    users = settings.base_users
    properties = settings.properties
    @task
    def hello_world(self):
        response = self.client.get("/api/users")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/json; charset=utf-8"
        data = response.json()["data"]
        assert all(prop in user for user in data for prop in self.properties)
        assert all(actualUser == expectedUser for expectedUser in self.users.values() for actualUser in data if actualUser["id"] == expectedUser["id"])
