import http from 'k6/http';
import { sleep, check } from 'k6';
import { users, properties } from '../test_data/users.js';

export const options = {
    thresholds: {
        http_req_duration: ["p(99) < 2000", "p(90) < 1000"],
        http_req_failed: ["rate < 0.01"],
    },
    stages: [
        { duration: "1m", target: 15 },
        { duration: "2m", target: 15 },
        { duration: "30s", target: 0 },
    ]
};


export default function () {
    let response = http.get("https://reqres.in/api/users");
    check(response, {
        'is status 200': (r) => r.status === 200,
        'header verification': (r) => r.headers["Content-Type"] === "application/json; charset=utf-8",
        'properties verification': (r) => {
            let data = JSON.parse(r.body)["data"];
            return data.every(user => properties.every(prop => prop in user));
          },
        'user data verification': (r) => {
            let data = JSON.parse(r.body)["data"];
            return Object.values(users).every(expectedUser => {
              let actualUser = data.find(user => user.id === expectedUser.id);
              return actualUser && JSON.stringify(actualUser) === JSON.stringify(expectedUser);
            });
          },
    });
    sleep(Math.random() * 5); 
};
