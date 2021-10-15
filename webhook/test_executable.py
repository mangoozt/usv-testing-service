import datetime
import logging
import os
import re
import time

import requests

from run_cases import test_usv

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

csrfmiddlewaretoken_re = re.compile('<input type="hidden" name="csrfmiddlewaretoken" value="([^"]+)">')


def upload_results(url, report_filename, title, commit_sha1='', commit_date='', build_number=''):
    files = {'file': open(report_filename, 'rb')}
    values = {'title': title,
              'commit_sha1': commit_sha1,
              'commit_date': commit_date,
              'build_number': build_number,
              }
    s = requests.Session()
    r = s.get(url)

    values['csrfmiddlewaretoken'] = csrfmiddlewaretoken_re.search(r.text).group(1)

    r = s.post(url, files=files, data=values)

    logging.info(f'Response code: {r.status_code}')


def test_executable(executable, working_dir='.', extra_arguments=None):
    if extra_arguments is None:
        extra_arguments = []

    report_filename = os.path.join('./reports', "report_" + str(datetime.datetime.now()) + ".parquet")

    report = test_usv(executable, working_dir, extra_arguments=extra_arguments)
    logging.info(f"Start saving report to '{report_filename}'")
    t_save = time.time()
    report.save_file(report_filename)
    logging.info(f'Save time: {time.time() - t_save}')
    return report_filename


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="USV executable cases test utility")
    parser.add_argument("executable", type=str, help="Path to USV executable")
    parser.add_argument("--working_dir", type=str, help="Path working dir with cases or metainfo.csv")
    parser.add_argument("--url", type=str, help="Url for results uploading", required=False, default='')
    parser.add_argument("--title", type=str, help="Title to pass to dashboard", required=False, default='')
    parser.add_argument("--sha1", type=str, help="Commit sha1", required=False, default='')
    parser.add_argument("--datetime", type=str, help="Commit datetime", required=False, default='')
    parser.add_argument("--build", type=str, help="Build number", required=False, default='')

    args, extra_args = parser.parse_known_args()

    if len(extra_args) > 0 and extra_args[0] != "--":
        extra_args = []
    else:
        extra_args = extra_args[1:]

    usv_executable = os.path.abspath(args.executable)

    if args.working_dir is not None:
        work_dir = os.path.abspath(args.working_dir)
    else:
        work_dir = os.path.abspath(os.getcwd())

    report_file = test_executable(usv_executable, working_dir=work_dir, extra_arguments=extra_args)
    if len(args.url) > 0:
        logging.info(f'Sending report file: `{report_file}`')
        upload_results(args.url, report_file, title=args.title, commit_sha1=args.sha1, commit_date=args.datetime,
                       build_number=args.build)
