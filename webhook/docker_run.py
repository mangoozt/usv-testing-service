import os

import docker


def run_tests_in_docker(execuatable_zip):
    image_name = os.getenv('TEST_RUNNER_IMAGE')
    client = docker.from_env()
    print(client.containers.run(image_name, ["python3", "run.py", execuatable_zip], detach=True, network="usv-testing-service_default",tmpfs='/app/tmp', mount=''))
    pass
