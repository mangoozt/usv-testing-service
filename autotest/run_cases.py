#!/usr/bin/env python3
import ctypes
import json
import os
import subprocess
import time
from datetime import datetime, date
from multiprocessing import Pool
from pathlib import Path

import pandas as pd
from geographiclib.geodesic import Geodesic
from natsort import natsorted

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
        self.tmpdir = os.path.join(self.work_dir, ".bks_report\\")
        self.rvo = None
        self.nopic = None
        self.fast = False

    def generate(self, data_directory, glob='*', rvo=None, nopic=False):
        self.rvo = rvo
        self.nopic = nopic
        directories_list = []
        try:
            df = pd.read_csv(data_directory + '/metainfo.csv', index_col=False)
            directories_list = df['datadirs'].values
        except FileNotFoundError:
            if not self.fast:
                for path in Path(data_directory).glob(glob):
                    for root, dirs, files in os.walk(path):
                        if "nav-data.json" in files or 'navigation.json' in files:
                            directories_list.append(os.path.join(data_directory, root))
                directories_list = natsorted(directories_list)
                df = pd.DataFrame()
                df['datadirs'] = directories_list
                df.to_csv(data_directory + '/metainfo.csv')
            else:
                dirs = os.listdir(data_directory)
                directories_list = [os.path.abspath(p) for p in dirs]

        with Pool() as p:
            cases = p.map(self.run_case, directories_list)

        return Report(cases, self.exe, self.work_dir, self.rvo)

    def generate_for_list(self, list, nopic=False):
        self.nopic = nopic
        with Pool() as p:
            cases = p.map(self.run_case, list)
        return Report(cases, self.exe, self.work_dir, self.rvo)

    def run_case(self, datadir):
        working_dir = os.path.abspath(os.getcwd())
        os.chdir(datadir)

        if os.path.exists(CASE_FILENAMES['nav_data']):
            case_filenames = CASE_FILENAMES
        else:
            case_filenames = CASE_FILENAMES_KT
        # Get a list of old results
        cur_path = Path('.')
        file_list = list(cur_path.glob(case_filenames['maneuvers'])) + \
                    list(cur_path.glob(case_filenames['analyse']))

        for filePath in file_list:
            try:
                os.remove(filePath)
            except OSError:
                pass

        # Print the exit code.
        exec_time = time.time()
        command = [self.exe, "--target-settings", case_filenames['target_settings'],
                   "--targets", case_filenames['targets_data'],
                   "--settings", case_filenames['settings'],
                   "--nav-data", case_filenames['nav_data'],
                   "--hydrometeo", case_filenames['hydrometeo'],
                   "--constraints", case_filenames['constraints'],
                   "--route", case_filenames['route'],
                   "--maneuver", case_filenames['maneuvers'],
                   "--analyse", case_filenames['analyse'],
                   "--predict", case_filenames['targets_maneuvers'],
                   ("--rvo-enable" if self.rvo is True else "")]

        # Added to prevent freezing
        try:
            completedProc = subprocess.run(command,
                                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                           stdin=subprocess.PIPE, timeout=6)
            exec_time = time.time() - exec_time
            print("{} .Return code: {}. Exec time: {} sec"
                  .format(datadir, fix_returncode(completedProc.returncode), exec_time))
            image_data = ""
            nav_report = ""
            target_data = None
            try:
                with open("nav-report.json", "r") as f:
                    nav_report = json.dumps(json.loads(f.read()), indent=4, sort_keys=True)
            except FileNotFoundError:
                pass
            try:
                with open("target-data.json", "r") as f:
                    target_data = json.dumps(json.loads(f.read()), indent=4, sort_keys=True)
            except FileNotFoundError:
                pass
            os.chdir(working_dir)

            try:
                target_data = json.loads(target_data)
            except:
                return
            datadir_i = os.path.split(datadir)[1]
            dist1, dist2 = 0, 0
            course1, course2 = 0, 0
            peleng1, peleng2 = 0, 0
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
                    "proc": completedProc,
                    "image_data": image_data,
                    "exec_time": exec_time,
                    "nav_report": nav_report,
                    "command": command,
                    "code": fix_returncode(completedProc.returncode),
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
            print("TEST TIMEOUT ERR")
            exec_time = time.time() - exec_time
            os.chdir(working_dir)
            target_data = None
            try:
                with open("target-data.json", "r") as f:
                    target_data = json.dumps(json.loads(f.read()), indent=4, sort_keys=True)
            except FileNotFoundError:
                pass

            datadir_i = os.path.split(datadir)[1]
            dist1, dist2 = 0, 0
            course1, course2 = 0, 0
            peleng1, peleng2 = 0, 0
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
                    "proc": None,
                    "image_data": "",
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

    def save_excel(self, filename='report.xlsx'):
        df = pd.json_normalize(self.cases)
        try:
            df.to_excel(filename)
        except ValueError:
            df.to_csv(filename)

    def save_csv(self, filename='report.csv'):
        df = pd.json_normalize(self.cases)
        df.to_csv(filename)



    def get_danger_params(self, statuses):
        return [rec['datadir'] for rec in self.cases if rec['code'] in statuses]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="BKS report generator")
    parser.add_argument("executable", type=str, help="Path to USV executable")
    parser.add_argument("--glob", type=str, default='*', help="Pattern for scanned directories")

    parser.add_argument("--rvo", action="store_true", help="Run USV with --rvo")
    parser.add_argument("--nopic", action="store_true", help="")
    parser.add_argument("--working_dir", type=str, help="Path to USV executable")
    args = parser.parse_args()

    use_rvo = None
    if args.rvo:
        use_rvo = True

    if args.working_dir is not None:
        cur_dir = os.path.abspath(args.working_dir)
    else:
        cur_dir = os.path.abspath(os.getcwd())
    t0 = time.time()
    usv_executable = os.path.join(cur_dir, args.executable)
    report = ReportGenerator(usv_executable)
    print("Starting converstion...")
    report_out = report.generate(cur_dir, glob=args.glob, rvo=use_rvo, nopic=args.nopic)
    # print("Starting saving to HTML")
    # report_out.save_html("report.html")
    print("Starting saving to EXCEL")
    name = "./reports/report1_" + str(date.today()) + ".csv"
    # report_out.save_excel(name)
    report_out.save_csv(name)
    print(f'Total time: {time.time() - t0}')
