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
        **kwargs
    ):
        SUCCESS_TEMPLATE = (
            '[{"measurement": "%s","tags": {"hostname":"%s","requestName": "%s","requestType": "%s","status":"%s"'
            '},"time":"%s","fields": {"responseTime": "%s","responseLength":"%s"}'
            "}]"
        )

        FAIL_TEMPLATE = (
            '[{"measurement": "%s","tags": {"hostname":"%s","requestName": "%s","requestType": "%s","exception":"%s","status":"%s"'
            '},"time":"%s","fields": {"responseTime": "%s","responseLength":"%s"}'
            "}]"
        )

        if exception:
            json_string = FAIL_TEMPLATE % (
                "ResponseTable",
                hostname,
                name,
                request_type,
                exception,
                "fail",
                datetime.datetime.now(tz=pytz.UTC),
                response_time,
                response_length,
            )
        else:
            json_string = SUCCESS_TEMPLATE % (
                "ResponseTable",
                hostname,
                name,
                request_type,
                "success",
                datetime.datetime.now(tz=pytz.UTC),
                response_time,
                response_length,
            )
        client.write_points(json.loads(json_string), time_precision="ms")

    @events.test_stop.add_listener
    def on_test_stop(environment, **kw):
        SUMMARY_TEMPLATE = """
        [
            {
                "measurement": "%s",
                "tags": 
                    {
                        "hostname":"%s",
                        "test_name": "%s"
                    },
                "time":"%s",
                "fields": 
                    {
                        "fail_ratio": "%s",
                        "num_requests":"%s",
                        "num_failures":"%s",
                        "total_rps":"%s",
                        "min_response_time":"%s",
                        "max_response_time":"%s",
                        "median_response_time":"%s",
                        "avg_response_time":"%s"
                    }
            }
        ]
"""
        json_string = SUMMARY_TEMPLATE % (
            "SummaryTable",
            hostname,
            environment.locustfile,
            datetime.datetime.now(tz=pytz.UTC),
            environment.stats.total.fail_ratio,
            environment.stats.total.num_requests,
            environment.stats.total.num_failures,
            environment.stats.total.total_rps,
            environment.stats.total.min_response_time,
            environment.stats.total.max_response_time,
            environment.stats.total.median_response_time,
            environment.stats.total.avg_response_time,
        )
        client.write_points(json.loads(json_string), time_precision="ms")
