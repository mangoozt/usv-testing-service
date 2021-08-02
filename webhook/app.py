import os
import re
import time

import requests
from flask import Flask, request, Response
from artifacts import load_artifacts, check_workflow_url
from run_cases import test_usv_archived
from threading import Thread

app = Flask(__name__)
token = os.getenv('GITHUB_TOKEN')
repo = os.getenv('GIHUB_REPO_URL')
workflow_name = os.getenv('GIHUB_WORKFLOW_LABEL')


def postpone(function):
    """
    Decorator for multitasking
    :param function:
    :return:
    """

    def decorator(*args, **kwargs):
        t = Thread(target=function, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()

    return decorator


csrfmiddlewaretoken_re = re.compile('<input type="hidden" name="csrfmiddlewaretoken" value="([^"]+)">')


@postpone
def process_workflow(json):
    if json['workflow_job']['name'] != workflow_name:
        return None
    if json['workflow_job']['status'] == 'completed' and json['workflow_job']['conclusion'] == 'success':
        if check_workflow_url(json['workflow_job']['url'], repo):
            time.sleep(1500)
            artifact = load_artifacts(json['workflow_job']['run_url'], token, '/tmp')
            if artifact is not None:
                report_file = test_usv_archived(artifact, './cases')

                files = {'file': open(report_file, 'rb')}
                values = {'title': json['workflow_job']['head_sha']}

                s = requests.Session()
                r = s.get('http://nginx/upload/')

                values['csrfmiddlewaretoken'] = csrfmiddlewaretoken_re.search(r.text).group(1)

                r = s.post('http://nginx/upload/', files=files, data=values)

                os.remove(report_file)
            else:
                print('No artifact')

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
