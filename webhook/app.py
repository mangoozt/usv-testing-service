import os

from flask import Flask, request, Response
from artifacts import load_artifacts, check_workflow_url
from docker_run import run_tests_in_docker

app = Flask(__name__)
token = os.getenv('GITHUB_TOKEN')
repo = os.getenv('GIHUB_REPO_URL')
workflow_name = os.getenv('GIHUB_WORKFLOW_LABEL')


def process_workflow(json):
    if json['workflow_job']['name'] != workflow_name:
        return None
    if json['workflow_job']['status'] == 'completed' and json['workflow_job']['conclusion'] == 'success':
        if check_workflow_url(json['workflow_job']['url'], repo):
            artifact = load_artifacts(json['workflow_job']['url'], token)
            if artifact is not None:
                pass

    return None


# @cross_origin()
@app.route('/github/payload', methods=['POST'])
def playload():
    json = request.get_json()
    print(json)
    try:
        if "workflow_job" in json and json["action"] == 'completed':
            process_workflow(json)
    except Exception as e:
        return Response(e.args, status=500)

    return Response(request.get_data(), mimetype='text/plain')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8001)
