import requests


def get_commit(repo_url, commit_sha1, token):
    with requests.Session() as session:
        session.headers = {'Authorization': f'token {token}',
                           'accept': 'application/vnd.github.v3+json',
                           'User-Agent': 'Awesome-Octocat-App'}

        result = session.get(url=repo_url)
        if not result.ok or result.status_code != 200:
            return None

        repo_json = result.json()
        commits_url = repo_json['commits_url']
        result = session.get(url=commits_url.replace('{/sha}', '/'+commit_sha1))

        if result.ok and result.status_code == 200:
            return result.json()

        return None
