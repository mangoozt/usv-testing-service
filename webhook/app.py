from datetime import date

import iso8601
import os
import re
import time

import requests
from flask import Flask, request, Response
from artifacts import load_artifacts, check_workflow_url, get_commit
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


def elipsis(content, length=50, suffix='...'):
    if len(content) <= length:
        return content
    else:
        return ' '.join(content[:length + 1].split(' ')[0:-1]) + suffix


@postpone
def process_workflow(json):
    if json['workflow_job']['name'] != workflow_name:
        return None
    if json['workflow_job']['status'] == 'completed' and json['workflow_job']['conclusion'] == 'success':
        if check_workflow_url(json['workflow_job']['url'], repo):

            artifact = None
            i = 0
            while artifact is None and i < 10:
                print("Waiting 10 sec for artifacts processing")
                time.sleep(10)
                artifact = load_artifacts(json['workflow_job']['run_url'], token, './tmp')
                i += 1

            if artifact is not None:
                print("Got artifact")
                report_file = os.path.join('./reports', "report_" + str(datetime.datetime.now()) + ".parquet")
                report_file = test_usv_archived(artifact, './cases', report_file=report_file, file_format='parquet')
                files = {'file': open(report_file, 'rb')}

                head_sha: str = json['workflow_job']['head_sha']
                commit_url = json['repository']['git_commits_url'].replace('{/sha}', "/" + head_sha)
                commit_json = get_commit(commit_url, token=token)

                commit_author = commit_json['author']
                commit_message = elipsis(commit_json['message'])
                commit_datetime = iso8601.parse_date(commit_author['date'])
                title = f"{commit_datetime} {head_sha[:7]} - {commit_message}"

                values = {'title': title}

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
