import re
import requests
import os


def get_filename_from_cd(cd):
    """
    Get filename from content-disposition
    """
    if not cd:
        return None
    name = re.findall('filename=([^;]+)', cd)
    if len(name) == 0:
        return None
    return name[0]


def check_workflow_url(workflow_url, repo_url):
    return workflow_url.find(repo_url) == 0


def load_artifacts(workflow_url, token, directory='.'):
    with requests.Session() as session:
        session.headers = {'Authorization': f'token {token}',
                           'accept': 'application/vnd.github.v3+json',
                           'User-Agent': 'Awesome-Octocat-App'}

        result = session.get(url=f"{workflow_url}/artifacts")
        result_json = result.json()

        if result.ok and result.status_code == 200:
            try:
                url = result_json['artifacts'][0]['archive_download_url']
                r = session.get(url, allow_redirects=True)
                filename = get_filename_from_cd(r.headers.get('content-disposition'))
                if filename is not None:
                    filename = os.path.abspath(os.path.join(directory, filename))
                    open(filename, 'wb').write(r.content)
                    return filename
            except KeyError or IndexError:
                print("No artifacts")
        return None

