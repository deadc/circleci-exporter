# circleci-exporter [![CircleCI](https://circleci.com/gh/grupozap/circleci-exporter.svg?style=svg)](https://circleci.com/gh/grupozap/circleci-exporter)

circleci-exporter provides build metrics from CircleCI, exposing these metrics for Prometheus.

### CircleCI Metrics

* **circleci_last_build_date**
	* Provides the last datetime build of a project (unixtime)
	
* **circleci_last_build_number**
	* Provides the last build number of a project
	
* **circleci_last_build_time_millis**
	* Provides the duration of a build in miliseconds
	
* **circleci_last_build_status**
	* Provides the last build status of a project
	
##### Labels

* project_name
	* The name of project

* branch
	* The branch where the build has been started

* started_by
	* The user who started

### Build Status numbers

Below the return numbers according to the build status from `circleci_last_build_status`

| status | number |
|--|--|
|retried             |12|
|canceled            |11|
|infrastructure_fail |10|
|timedout            | 9|
|not_run             | 8|
|running             | 7|
|queued              | 6|
|scheduled           | 5|
|not_running         | 4|
|no_tests            | 3|
|fixed               | 2|
|failed              | 1|
|success             | 0|

### Variables

  * CIRCLE_TOKEN (needed)
    * The token from CircleCI with read access and followed projects configured.

  * CIRCLE_PROJECTS
    * The projects you will read for metrics (comma separated), by default the exporter gets all projects based on followed projects. eg: CIRCLE_PROJECTS=app1,app2,app3

  * CIRCLE_USERNAME
    * The username for access of a project, if you have multiple groups access, you need to set this based on CIRCLE_PROJECTS

### How to build

    $ docker build . -t vivareal/circleci-exporter

### How to run

You will need `K8S_TOKEN` and `K8S_ENDPOINT` to access the api-server
	
    $ export CIRCLE_TOKEN=1ca308df6cdb0a8bf40d59be2a17eac1
    $ docker run -p 5000:5000 -e "CIRCLE_TOKEN=${CIRCLE_TOKEN}" vivareal/circleci-exporter

### How to deploy

Set you target k8s context and apply the deployment files

    $ kubectl apply -f deploy/

