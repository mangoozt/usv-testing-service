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

from generator import Generator, generate_metadata

CASE_FILENAMES = {'nav_data': 'nav-data.json',
                  'maneuvers': 'maneuver.json',
                  'targets_data': 'target-data.json',
                  'target_settings': 'target-settings.json',
                  'targets_maneuvers': 'target-maneuvers.json',
                  'targets_real': 'real-target-maneuvers.json',
                  'analyse': 'nav-report.json',
                  'constraints': 'constraints.json',
                  'route': 'route-data.json',
                  'settings': 'settings.json',
                  'hydrometeo': 'hmi-data.json'}

CASE_FILENAMES_KT = {'nav_data': 'navigation.json',
                     'maneuvers': 'result_maneuver.json',
                     'targets_data': 'targets.json',
                     'target_settings': 'targets_settings.json',
                     'targets_maneuvers': 'predicted_tracks.json',
                     'targets_real': 'real-target-maneuvers.json',
                     'analyse': 'evaluation.json',
                     'constraints': 'constraints.json',
                     'route': 'route.json',
                     'settings': 'settings.json',
                     'hydrometeo': 'hydrometeo.json'}


def fix_returncode(code):
    return ctypes.c_int32(code).value


class ReportGenerator:
    def __init__(self, executable):
        self.exe = executable
        self.cases = []
        self.work_dir = os.path.abspath(os.getcwd())
        self.tmpdir = None
        self.rvo = None
        self.nopic = None
        self.fast = False

    def generate(self, data_directory, glob='*', rvo=None, nopic=False):
        self.tmpdir = tempfile.mkdtemp(prefix=os.path.join(os.getcwd(), 'tmp/'))
        self.rvo = rvo
        self.nopic = nopic
        directories_list = []

        if not os.path.exists(data_directory + '/metainfo.csv'):
            _df = generate_metadata(data_directory)
            print("Metainfo generated")
        else:
            _df = pd.read_csv(data_directory + '/metainfo.csv', index_col=False)
            print("Metainfo loaded")

        _df['datadir'] = [os.path.join(data_directory, x) for x in _df['datadir']]

        t0 = time.time()
        print('Converting df to list')
        df_list = _df.T.to_dict().values()
        print('Converting time: ', time.time() - t0)
        print('Testing in parallel')
        t0 = time.time()
        with Pool() as p:
            cases = p.map(self.run_case, df_list)
        print('Testing time: ', time.time() - t0)
        print('Clean tmp')
        t0 = time.time()
        shutil.rmtree(self.tmpdir)
        print('Clean time: ', time.time() - t0)
        return Report(cases, self.exe, self.work_dir, self.rvo)

    def generate_for_list(self, case_list, nopic=False):
        self.nopic = nopic
        with Pool() as p:
            cases = p.map(self.run_case, case_list)
        return Report(cases, self.exe, self.work_dir, self.rvo)

    def run_case(self, df_case):
        working_dir = os.path.abspath(os.getcwd())
        case = df_case
        datadir = case['datadir']

        usetmp = False
        if False and case['dist1'] != 0:

            gen = Generator(safe_div_dist=1)
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
            datadir = (os.path.join(self.tmpdir, os.path.split(datadir)[-1]))
            gen.our_vel = case["speed"]

            gen.construct_files(datadir, targets)
            usetmp = True

        os.chdir(datadir)

        if os.path.exists(CASE_FILENAMES['nav_data']):
            case_filenames = CASE_FILENAMES
        else:
            case_filenames = CASE_FILENAMES_KT
        # Get a list of old results
        cur_path = Path('.')
        file_list = list(cur_path.glob(case_filenames['maneuvers'])) + list(cur_path.glob(case_filenames['analyse']))

        for filePath in file_list:
            try:
                os.remove(filePath)
            except OSError:
                pass

        # Print the exit code.
        exec_time = time.time()

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
                   "--predict", targets_maneuver_file,
                   ("--rvo-enable" if self.rvo is True else "")]

        # Added to prevent freezing
        try:
            completed_proc = subprocess.run(command,
                                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                            stdin=subprocess.PIPE, timeout=6)
            exec_time = time.time() - exec_time
            # print("{} .Return code: {}. Exec time: {} sec".format(datadir, fix_returncode(completed_proc.returncode),
            #                                                       exec_time))

            image_data = ""
            nav_report = ""
            target_data = None
            try:
                with open(analyse_file, "r") as f:
                    nav_report = json.dumps(json.loads(f.read()), indent=4, sort_keys=True)
            except FileNotFoundError:
                pass
            try:
                with open("target-data.json", "r") as f:
                    target_data = json.dumps(json.loads(f.read()), indent=4, sort_keys=True)
            except FileNotFoundError:
                pass
            os.chdir(working_dir)
            if usetmp:
                shutil.rmtree(datadir)

            try:
                target_data = json.loads(target_data)
            except:
                return
            datadir_i = os.path.split(datadir)[1]
            lat, lon = 0, 0
            try:
                with open(datadir + "/nav-data.json", "r") as f:
                    nav_d = json.loads(f.read())
                    lat, lon = nav_d['lat'], nav_d['lon']
            except FileNotFoundError:
                pass
            try:
                dist1, course1, peleng1 = self.get_target_params(lat, lon, target_data[0])
            except IndexError or TypeError:
                dist1, course1, peleng1 = 0, 0, 0
            try:
                dist2, course2, peleng2 = self.get_target_params(lat, lon, target_data[1])
            except IndexError or TypeError:
                dist2, course2, peleng2 = 0, 0, 0

            types, right = self.load_maneuver(datadir)
            if len(types) == 1:
                types.append(None)

            return {"datadir": datadir_i,
                    "exec_time": exec_time,
                    "nav_report": nav_report,
                    "command": command,
                    "code": fix_returncode(completed_proc.returncode),
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

        except subprocess.TimeoutExpired:
            print("TEST TIMEOUT ERR:", datadir)
            exec_time = time.time() - exec_time
            os.chdir(working_dir)
            if usetmp:
                shutil.rmtree(datadir)

            target_data = None
            try:
                with open("target-data.json", "r") as f:
                    target_data = json.dumps(json.loads(f.read()), indent=4, sort_keys=True)
            except FileNotFoundError:
                pass

            datadir_i = os.path.split(datadir)[1]
            lat, lon = 0, 0
            try:
                with open(datadir + "/nav-data.json", "r") as f:
                    nav_d = json.loads(f.read())
                    lat, lon = nav_d['lat'], nav_d['lon']
            except FileNotFoundError:
                pass
            try:
                dist1, course1, peleng1 = self.get_target_params(lat, lon, target_data[0])
            except:
                dist1, course1, peleng1 = 0, 0, 0
            try:
                dist2, course2, peleng2 = self.get_target_params(lat, lon, target_data[1])
            except:
                dist2, course2, peleng2 = 0, 0, 0

            return {"datadir": datadir_i,
                    "exec_time": exec_time,
                    "nav_report": None,
                    "command": command,
                    "code": 6,
                    "dist1": dist1,
                    "dist2": dist2,
                    "course1": course1,
                    "course2": course2,
                    "peleng1": peleng1,
                    "peleng2": peleng2,
                    "right": None,
                    "type1": None,
                    "type2": None
                    }

    def load_maneuver(self, datadir):
        """
        Returns turn direction and scenarios types.
        @param datadir: data directory.
        @return: array with target types and turn direction.
        """
        try:
            c_dif = 0
            with open(datadir + "/maneuver.json", "r") as f:
                maneuver = json.loads(f.read())
                parts = maneuver[0]['path']['items']
                start_angle = parts[0]['begin_angle']
                for part in parts:
                    if part['begin_angle'] != start_angle:
                        c_dif = part['begin_angle'] - start_angle
                        break
            #         if c_dif < 0 -> left, else right
            #         right = True
            types = []
            with open(datadir + "/nav-report.json", "r") as f:
                report = json.loads(f.read())
                targets = report['target_statuses']
                for target in targets:
                    types.append(target['scenario_type'])
            return types, c_dif > 0
        except FileNotFoundError:
            return [None], None

    def get_target_params(self, lat, lon, target_data):
        lat_t, lon_t = target_data["lat"], target_data["lon"]
        path = Geodesic.WGS84.Inverse(lat, lon, lat_t, lon_t)
        dist = path['s12'] / 1852
        course = target_data["COG"]
        peleng = path['azi1']
        return dist, course, peleng


class Report:

    def __init__(self, cases, executable, work_dir, rvo):
        self.cases = cases
        self.exe = executable
        self.work_dir = work_dir
        self.rvo = rvo

    def save_file(self, filename='report.xlsx'):
        df = pd.json_normalize(self.cases)
        df.drop(columns=['command', 'nav_report'], inplace=True)
        try:
            file_extension = filename.split('.')[-1]
            if file_extension == 'parquet':
                df.to_parquet(filename)
            elif file_extension == 'xlsx':
                df.to_excel(filename)
            else:
                df.to_csv(filename)
        except ValueError:
            df.to_csv(filename)

    def get_danger_params(self, statuses):
        return [rec['datadir'] for rec in self.cases if rec['code'] in statuses]


def test_usv_archived(archive, cases_dir, report_file=None, file_format='csv'):
    import zipfile
    tmpdir = tempfile.mkdtemp(prefix=os.getcwd() + '/')
    with zipfile.ZipFile(archive, 'r') as zip_ref:
        zip_ref.extractall(tmpdir)
    executable = os.path.join(tmpdir, 'usv')
    result = None
    if os.path.exists(executable):
        os.chmod(executable, 0o777)
        result = test_usv(executable, cases_dir, report_file, file_format=file_format)
    shutil.rmtree(tmpdir)
    return result


def test_usv(executable, cases_dir, report_file=None, file_format='csv'):
    t0 = time.time()
    report = ReportGenerator(executable)
    print("Starting converstion...")
    report_out = report.generate(cases_dir)
    print(f'Finished in {time.time() - t0} sec')
    t_save = time.time()
    if report_file is None:
        report_file = os.path.join(cases_dir, "report1_" + str(date.today()) + "." + file_format)

    print(f"Starting saving report to '{report_file}'")
    report_out.save_file(report_file)
    print(f'Save time: {time.time() - t_save}')
    print(f'Total time: {time.time() - t0}')
    return report_file


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="BKS report generator")
    parser.add_argument("executable", type=str, help="Path to USV executable")
    parser.add_argument("--glob", type=str, default='*', help="Pattern for scanned directories")

    parser.add_argument("--working_dir", type=str, help="Path to USV executable")
    parser.add_argument("--report_file", type=str, help="Report file")
    args = parser.parse_args()

    if args.working_dir is not None:
        cur_dir = os.path.abspath(args.working_dir)
    else:
        cur_dir = os.path.abspath(os.getcwd())
    usv_executable = os.path.abspath(args.executable)
    test_usv(usv_executable, cur_dir, args.report_file)
