import os
import time
import datetime
import threading
import prometheus_client
import requests_cache

from dateutil.parser import parse
from flask import Response, Flask, request
from prometheus_client.core import CollectorRegistry
from prometheus_client import Gauge
from circleci import api

# keep 30m cache from CircleCI
requests_cache.install_cache(cache_name='circleci', backend='sqlite', expire_after=1800)

def convert_to_timestamp(input_date):
    return time.mktime(parse(input_date).timetuple()) if input_date else None

def list_followed_projects(projects, username):
    if projects is None or username is None:
        return circle_api.get_projects()

    projects = [ project for project in projects.split(',') ]
    return [ {"reponame" : project, "username": username} for project in projects ]

def get_metrics(project):
    project_summary = circle_api.get_project_build_summary(
        username = project["username"],
        project  = project["reponame"],
        limit    = 1,
        offset   = 0
    )
    return project_summary[0] if len(project_summary) > 0 else None

def add_last_build_date(metric, project):
    if project["start_time"] is not None:
        value = convert_to_timestamp(project["start_time"])
        
        metric_copy = {k:v for k,v in metric._metrics.items() if v}
        for detail, object in metric_copy.items():
            if detail[0] != project["reponame"]:
                continue
            if detail[2] != project["user"]["login"]:
                metric.remove(*detail)

        metric.labels(
            project_name      = '{}'.format(project["reponame"]),
            branch            = '{}'.format(project['branch']),
            started_by        = '{}'.format(project["user"]["login"])
        ).set(value)

def add_last_build_status(metric, project):
    if project["status"] is None:
        return None

    value = {
        'retried':             12,
        'canceled':            11,
        'infrastructure_fail': 10,
        'timedout':             9,
        'not_run':              8,
        'running':              7,
        'queued':               6,
        'scheduled':            5,
        'not_running':          4,
        'no_tests':             3,
        'fixed':                2,
        'failed':               1,
        'success':              0
    }
    value = value.get(project["status"])

    metric_copy = {k:v for k,v in metric._metrics.items() if v}
    for detail, object in metric_copy.items():
        if detail[0] != project["reponame"]:
            continue
        if detail[2] != project["user"]["login"]:
            metric.remove(*detail)

    metric.labels(
        project_name      = '{}'.format(project["reponame"]),
        branch            = '{}'.format(project['branch']),
        started_by        = '{}'.format(project["user"]["login"])
    ).set(value)

def add_last_build_time_millis(metric, project):
    if project["build_time_millis"]:
        value = project['build_time_millis']

        metric_copy = {k:v for k,v in metric._metrics.items() if v}
        for detail, object in metric_copy.items():
            if detail[0] != project["reponame"]:
                continue
            if detail[2] != project["user"]["login"]:
                metric.remove(*detail)

        metric.labels(
            project_name      = '{}'.format(project["reponame"]),
            branch            = '{}'.format(project['branch']),
            started_by        = '{}'.format(project["user"]["login"])
        ).set(value)

def add_last_build_number(metric, project):
    if project["build_num"]:
        value = project['build_num']
        
        metric_copy = {k:v for k,v in metric._metrics.items() if v}
        for detail, object in metric_copy.items():
            if detail[0] != project["reponame"]:
                continue
            if detail[2] != project["user"]["login"]:
                metric.remove(*detail)

        metric.labels(
            project_name      = '{}'.format(project["reponame"]),
            branch            = '{}'.format(project['branch']),
            started_by        = '{}'.format(project["user"]["login"])
        ).set(value)

def generate_metrics(projects):
    for project in projects:
        project_summary = get_metrics(project)
        add_last_build_date(last_build_date, project_summary)
        add_last_build_number(last_build_number, project_summary)
        add_last_build_time_millis(last_build_time_millis, project_summary)
        add_last_build_status(last_build_status, project_summary)

app = Flask(__name__)

circle_api = api.Api(os.environ.get('CIRCLE_TOKEN'))
projects = list_followed_projects(projects=os.environ.get('CIRCLE_PROJECTS'), username=os.environ.get('CIRCLE_USERNAME'))

last_build_date = Gauge('circleci_last_build_date', 'Last datetime of build of a project', ['project_name', 'started_by', 'branch'])
last_build_number = Gauge('circleci_last_build_number', 'Last build number of a project', ['project_name', 'branch', 'started_by'])
last_build_time_millis = Gauge('circleci_last_build_time_millis', 'Duration of last build of a project', ['project_name', 'branch', 'started_by'])
last_build_status = Gauge('circleci_last_build_status', 'Last build status of a project', ['project_name', 'branch', 'started_by'])

@app.route("/health", methods=["GET"])
def healthcheck():
    return "OK"

@app.route("/metrics")
def requests_count():
    result_metrics = []

    thr = threading.Thread(target=generate_metrics, args=(projects,))

    # UGLY (WONG) WORKAROUND
    if threading.active_count() <= 3:
        thr.start()

    result_metrics.append(prometheus_client.generate_latest(last_build_date))
    result_metrics.append(prometheus_client.generate_latest(last_build_number))
    result_metrics.append(prometheus_client.generate_latest(last_build_time_millis))
    result_metrics.append(prometheus_client.generate_latest(last_build_status))

    return Response(result_metrics, mimetype="text/plain")

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
