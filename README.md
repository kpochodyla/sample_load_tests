# API Load Tests
This project is an example of API load testing with the Reqres API using [k6](https://k6.io/) and [Grafana](https://grafana.com/).
So far, only one test has been created because my main goal was to become more familiar with Grafana and the dashboards that can be created using data from load testing. If you are interested in other possible integrations of `k6` with different tools, you may check the [official documentation](https://k6.io/docs/integrations/)  
## Requirements
To run this test on your machine, you are required to have `k6` installed. To integrate the results of tests with Grafana, you can use the `--out` flag when running the test (I personally do it by sending the output to influxdb, which is later used as a data source in Grafana).
## Running Tests
After installing `k6` you can simply run the test with:
`k6 run tests/test_get_list_of_users.js`
If you want to have the output sent to influxdb, an example of the test execution would look like this:
`k6 run --out influxdb=http://192.168.0.171:8086/k6_data tests/test_get_list_of_users.js`
