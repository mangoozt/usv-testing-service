#!/usr/bin/env python3
import ctypes
import json
import os
import shutil
import subprocess
import tempfile
import time
from datetime import date
from multiprocessing import Pool
from pathlib import Path
import pandas as pd
from geographiclib.geodesic import Geodesic
import logging

from generator import Generator, generate_metadata, CASE_FILENAMES, CASE_FILENAMES_KT, CASE_FILENAMES_VSE

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)


def fix_return_code(code):
    return ctypes.c_int32(code).value


def generate_case_files(case, datadir, safe_diverg_dist=1):
    gen = Generator(safe_div_dist=safe_diverg_dist)
    targets = []
    if case["dist1"] != 0:
        targets.append({"peleng": case["peleng1"],
                        "dist": case["dist1"],
                        "c_diff": case["course1"],
                        "v_target": case["speed1"]})
    if case["dist2"] != 0:
        targets.append({"peleng": case["peleng2"],
                        "dist": case["dist2"],
                        "c_diff": case["course2"],
                        "v_target": case["speed2"]})

    gen.our_vel = case["speed"]
    os.makedirs(datadir, exist_ok=True)
    gen.construct_files(datadir, targets)


def load_maneuver(maneuver_file, analyse_file):
    """
    Returns turn direction and scenarios types.
    @param maneuver_file: maneuver file name
    @param analyse_file: analyse file name
    @return: array with target types and turn direction.
    """
    right = None
    try:
        with open(maneuver_file, "r") as f:
            maneuver = json.loads(f.read())
            parts = maneuver[0]['path']['items']
            start_angle = parts[0]['begin_angle']
            for part in parts:
                if part['begin_angle'] != start_angle:
                    c_dif = part['begin_angle'] - start_angle
                    right = c_dif > 0
                    break
        #         if c_dif < 0 -> left, else right
        #         right = True
    except FileNotFoundError:
        pass
    types = []
    try:
        with open(analyse_file, "r") as f:
            report = json.loads(f.read())
            targets = report['target_statuses']
            for target in targets:
                types.append(target['scenario_type'])

    except FileNotFoundError:
        pass

    return types, right


def get_target_params(lat, lon, target_data):
    lat_t, lon_t = target_data["lat"], target_data["lon"]
    path = Geodesic.WGS84.Inverse(lat, lon, lat_t, lon_t)
    dist = path['s12'] / 1852
    course = target_data["COG"]
    peleng = path['azi1']
    return dist, course, peleng


class ReportGenerator:
    def __init__(self, executable):
        self.exe = executable
        self.cases = []
        self.work_dir = os.path.abspath(os.getcwd())
        self.tmpdir = None
        self.extra_args = []
        self.fast = False

    def generate(self, data_directory, extra_arguments=None):
        if extra_arguments is None:
            extra_arguments = []
        self.tmpdir = tempfile.mkdtemp(prefix=os.path.join(os.getcwd(), 'tmp/'))
        self.extra_args = extra_arguments

        if not os.path.exists(data_directory + '/metainfo.csv'):
            _df = generate_metadata(data_directory)
            logging.info("Metainfo generated")
        else:
            _df = pd.read_csv(data_directory + '/metainfo.csv', index_col=False)
            logging.info("Metainfo loaded")

        _df['datadir'] = [os.path.join(data_directory, x) for x in _df['datadir']]

        t0 = time.time()
        logging.info('Converting df to list')
        df_list = list(_df.T.to_dict().values())
        logging.info(f'Converting time: {time.time() - t0}')
        logging.info('Testing in parallel')
        t0 = time.time()
        with Pool() as p:
            cases_awt = p.imap_unordered(self.run_case, df_list)
            cases = list(cases_awt)
        logging.info(f'Testing time: {time.time() - t0}')
        logging.info('Clean tmp')
        t0 = time.time()
        shutil.rmtree(self.tmpdir)
        logging.info(f'Clean time: {time.time() - t0}')
        return Report(cases, self.exe, self.work_dir, extra_arguments=self.extra_args)

    def run_case(self, df_case):
        working_dir = os.path.abspath(os.getcwd())
        case = df_case
        datadir = case['datadir']

        temp_dir = os.path.join(self.tmpdir, os.path.split(datadir)[-1])
        os.makedirs(temp_dir, exist_ok=True)
        if case['dist1'] != 0:
            datadir = temp_dir
            generate_case_files(case, datadir)

        os.chdir(datadir)

        if os.path.exists('nav-data.json') & os.path.exists('targets.json'):
            case_filenames = CASE_FILENAMES_VSE
        elif os.path.exists("navigation.json"):
            case_filenames = CASE_FILENAMES_KT
        else:
            case_filenames = CASE_FILENAMES

        # Get a list of old results
        cur_path = Path('.')
        file_list = list(cur_path.glob(case_filenames['maneuvers'])) + list(cur_path.glob(case_filenames['analyse']))

        for filePath in file_list:
            try:
                os.remove(filePath)
            except OSError:
                pass

        analyse_file = os.path.join(self.tmpdir, os.path.split(datadir)[-1], 'analyse')
        maneuver_file = os.path.join(self.tmpdir, os.path.split(datadir)[-1], 'maneuver')
        targets_maneuver_file = os.path.join(self.tmpdir, os.path.split(datadir)[-1], 'tagets')

        command = [self.exe, "--target-settings", case_filenames['target_settings'],
                   "--targets", case_filenames['targets_data'],
                   "--settings", case_filenames['settings'],
                   "--nav-data", case_filenames['nav_data'],
                   "--hydrometeo", case_filenames['hydrometeo'],
                   "--constraints", case_filenames['constraints'],
                   "--route", case_filenames['route'],
                   "--maneuver", maneuver_file,
                   "--analyse", analyse_file,
                   "--predict", targets_maneuver_file] + self.extra_args

        completed_proc = None
        exec_time = time.time()
        try:
            completed_proc = subprocess.run(command,
                                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                            stdin=subprocess.PIPE, timeout=3)
            exec_time = time.time() - exec_time
            code = fix_return_code(completed_proc.returncode)
        # Added to prevent freezing
        except subprocess.TimeoutExpired:
            code = 6
            exec_time = time.time() - exec_time

        nav_report = ""
        target_data = None
        try:
            with open(analyse_file, "r") as f:
                nav_report = json.dumps(json.loads(f.read()), indent=4, sort_keys=True)
        except FileNotFoundError:
            pass

        try:
            with open(case_filenames['targets_data'], "r") as f:
                target_data = json.dumps(json.loads(f.read()), indent=4, sort_keys=True)
        except FileNotFoundError:
            pass

        lat, lon = 0, 0
        try:
            with open(datadir + case_filenames["nav_data"], "r") as f:
                nav_d = json.loads(f.read())
                lat, lon = nav_d['lat'], nav_d['lon']
        except FileNotFoundError:
            pass

        dist1, course1, peleng1 = 0, 0, 0
        dist2, course2, peleng2 = 0, 0, 0

        if target_data is not None:
            try:
                target_data = json.loads(target_data)
            except TypeError:
                pass

            try:
                dist1, course1, peleng1 = get_target_params(lat, lon, target_data[0])
            except IndexError or TypeError:
                pass
            try:
                dist2, course2, peleng2 = get_target_params(lat, lon, target_data[1])
            except IndexError or TypeError:
                pass

        types, right = load_maneuver(maneuver_file, analyse_file)
        if len(types) == 0:
            types.append(None)
        if len(types) == 1:
            types.append(None)

        os.chdir(working_dir)

        if code not in (0, 1, 2, 3, 4, 5, 6):
            if completed_proc is not None:
                print(datadir, '\n', completed_proc.stdout, '\n', completed_proc.stderr)
        if code == 6:
            print(datadir, '\n', 'TIMEOUT')
        else:
            shutil.rmtree(temp_dir)

        data_dir_name = os.path.split(datadir)[1]
        return {"datadir": data_dir_name,
                "exec_time": exec_time,
                "nav_report": nav_report,
                "command": command,
                "code": code,
                "dist1": dist1,
                "dist2": dist2,
                "course1": course1,
                "course2": course2,
                "peleng1": peleng1,
                "peleng2": peleng2,
                "right": right,
                "type1": types[0],
                "type2": types[1]
                }


class Report:

    def __init__(self, cases, executable, work_dir, extra_arguments=None):
        if extra_arguments is None:
            extra_arguments = []
        self.cases = cases
        self.exe = executable
        self.work_dir = work_dir
        self.extra_args = extra_arguments

    def get_dataframe(self):
        cases_df = pd.json_normalize(self.cases)
        try:
            cases_df.drop(columns=['command'], inplace=True)
        except KeyError:
            pass
        try:
            cases_df.drop(columns=['nav_report'], inplace=True)
        except KeyError:
            pass
        return cases_df

    def save_file(self, filename='report.xlsx'):
        cases_df = self.get_dataframe()

        try:
            file_extension = filename.split('.')[-1]
            if file_extension == 'parquet':
                cases_df.to_parquet(filename)
            elif file_extension == 'xlsx':
                cases_df.to_excel(filename)
            else:
                cases_df.to_csv(filename)
        except ValueError:
            cases_df.to_csv(filename)

    def get_danger_params(self, statuses):
        return [rec['datadir'] for rec in self.cases if rec['code'] in statuses]


def test_usv_archived(archive, cases_dir):
    import zipfile
    tmpdir = tempfile.mkdtemp(prefix=os.getcwd() + '/')
    with zipfile.ZipFile(archive, 'r') as zip_ref:
        zip_ref.extractall(tmpdir)
    executable = os.path.join(tmpdir, 'usv')
    result = None
    if os.path.exists(executable):
        os.chmod(executable, 0o777)
        result = test_usv(executable, cases_dir)
    shutil.rmtree(tmpdir)
    return result


def test_usv(executable, cases_dir, extra_arguments=None):
    if extra_arguments is None:
        extra_arguments = []

    report_generator = ReportGenerator(executable)

    return report_generator.generate(cases_dir, extra_arguments=extra_arguments)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="BKS report generator")
    parser.add_argument("executable", type=str, help="Path to USV executable")
    parser.add_argument("--print_result", dest='print_result', action='store_true', help="Verbose cases output")
    parser.add_argument("--noreport", dest='noreport', action='store_true', help="Skip report saving")
    parser.add_argument("--failcode", dest='failcode', action='store_true', help="Non-zero code on failure")

    parser.add_argument("--working_dir", type=str, help="Path to USV executable")
    parser.add_argument("--report_file", type=str, help="Report file")

    args, extra_args = parser.parse_known_args()

    if len(extra_args) > 0 and extra_args[0] != "--":
        extra_args = []
    else:
        extra_args = extra_args[1:]

    if args.working_dir is not None:
        cur_dir = os.path.abspath(args.working_dir)
    else:
        cur_dir = os.path.abspath(os.getcwd())
    usv_executable = os.path.abspath(args.executable)

    logging.info("Start running cases...")
    time_start = time.time()
    report_out = test_usv(usv_executable, cur_dir, extra_arguments=extra_args)

    logging.info(f'Finished in {time.time() - time_start} sec')

    if not args.noreport:
        if args.report_file is None:
            report_file = os.path.join(cur_dir, f"report1_{date.today()}.csv")
        else:
            report_file = args.report_file

        logging.info(f"Start saving report to '{report_file}'")
        t_save = time.time()
        report_out.save_file(report_file)
        logging.info(f'Save time: {time.time() - t_save}')

    exitcode = 0
    if args.print_result or args.failcode:
        df = report_out.get_dataframe()
        if args.print_result:
            if len(df) > 0:
                with pd.option_context('display.max_rows', None, 'display.max_columns',
                                       None):  # more options can be specified also
                    print(df)
        if args.failcode and not df['code'].between(0, 1).all():
            exitcode = 2

    logging.info(f'Total time: {time.time() - time_start}')
    exit(exitcode)
