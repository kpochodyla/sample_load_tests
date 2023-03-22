from locust import HttpUser, task, between, events
from settings.settings import TestSettings
from influxdb import InfluxDBClient
import json
import datetime
import pytz
import socket
from settings.secrets import secrets

hostname = socket.gethostname()
client = InfluxDBClient(host=secrets.influxdb_hostname, port=secrets.influxdb_port)
client.switch_database("locust_data")


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
        assert all(
            actualUser == expectedUser
            for expectedUser in self.users.values()
            for actualUser in data
            if actualUser["id"] == expectedUser["id"]
        )

    @events.request.add_listener
    def my_request_handler(
        request_type,
        name,
        response_time,
        response_length,
        response,
        context,
        exception,
        start_time,
        url,
        **kwargs,
    ):
        if exception:
            json_string = f"""
                [
                    {{
                        "measurement": "ResponseTable",
                        "tags": 
                            {{
                                "hostname":" {hostname}",
                                "requestName": "{name}",
                                "requestType": "{request_type}",
                                "status": "fail",
                                "exception": "{exception}"
                            }},
                        "time":"{datetime.datetime.now(tz=pytz.UTC)}",
                        "fields": 
                            {{
                                "responseTime": {response_time},
                                "responseLength":{response_length}
                            }}
                    }}
                ]
            """
        else:
            json_string = f"""
                [
                    {{
                        "measurement": "ResponseTable",
                        "tags": 
                            {{
                                "hostname":"{hostname}",
                                "requestName": "{name}",
                                "requestType": "{request_type}",
                                "status": "success"
                            }},
                        "time":"{datetime.datetime.now(tz=pytz.UTC)}",
                        "fields": 
                            {{
                                "responseTime": {response_time},
                                "responseLength": {response_length}
                            }}
                    }}
                ]
            """
        client.write_points(json.loads(json_string), time_precision="ms")

    @events.test_stop.add_listener
    def on_test_stop(environment, **kw):
        SUMMARY_TEMPLATE = f"""
        [
            {{
                "measurement": "{secrets.influxdb_summary}",
                "tags": 
                    {{
                        "hostname": "{hostname}",
                        "test_name": "{environment.locustfile}"
                    }},
                "time": "{datetime.datetime.now(tz=pytz.UTC)}",
                "fields": 
                    {{
                        "fail_ratio": {environment.stats.total.fail_ratio},
                        "num_requests": {environment.stats.total.num_requests},
                        "num_failures": {environment.stats.total.num_failures},
                        "total_rps": {environment.stats.total.total_rps},
                        "min_response_time": {environment.stats.total.min_response_time},
                        "max_response_time": {environment.stats.total.max_response_time},
                        "median_response_time": {environment.stats.total.median_response_time},
                        "avg_response_time": {environment.stats.total.avg_response_time}
                    }}
            }}
        ]
"""
        client.write_points(json.loads(SUMMARY_TEMPLATE), time_precision="ms")
