import json
import math
import os
from dataclasses import make_dataclass
from pathlib import Path

import pandas as pd
from geographiclib.geodesic import Geodesic


class Frame:
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def from_wgs(self, lat, lon):
        """
        Converts WGS coords to local
        :param lat:
        :param lon:
        :return: x, y, distance, bearing
        """
        path = Geodesic.WGS84.Inverse(self.lat, self.lon, lat, lon)

        angle = math.radians(path['azi1'])
        dist = path['s12'] / 1852
        return dist * math.cos(angle), dist * math.sin(angle), dist, angle

    def to_wgs(self, x, y):
        """
        Converts local coords to WGS
        :param x:
        :param y:
        :return: lat, lon
        """
        azi1 = math.degrees(math.atan2(y, x))
        dist = (x ** 2 + y ** 2) ** .5
        path = Geodesic.WGS84.Direct(self.lat, self.lon, azi1, dist * 1852)
        return path['lat2'], path['lon2']

    def to_wgs_azi(self, azi1, dist):
        path = Geodesic.WGS84.Direct(self.lat, self.lon, azi1, dist * 1852)
        return path['lat2'], path['lon2']

    def dist_azi_to_point(self, lat, lon):
        path = Geodesic.WGS84.Inverse(self.lat, self.lon, lat, lon)
        return path['s12'] / 1852, path['azi1']


def det(a, b):
    """
    Pseudoscalar multiply of vectors
    :param a: 2D vector
    :param b: 2D vector
    :return: pseudoscalar multiply
    """
    return a.x * b.y - b.x * a.y


def calc_cpa_params(v, v0, R):
    """
    Calculating of CPA and tCPA criterions
    :param v: target speed, vector
    :param v0: our speed, vector
    :param R: relative position, vector
    :return:
    """
    w = v - v0
    cpa = abs(det(R, w) / abs(w))
    tcpa = - (R * w) / (w * w)
    return cpa, tcpa


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

PDCase = make_dataclass("Case", [("datadir", str),
                                 ("dist1", float), ("dist2", float),
                                 ("course1", float), ("course2", float),
                                 ("speed1", float), ("speed2", float),
                                 ("peleng1", float), ("peleng2", float),
                                 ("safe_diverg", float),
                                 ("speed", float)])


def get_metadata(case_directory):
    bare_name = os.path.split(case_directory)[-1]
    split = bare_name.split('_')

    datadir = (case_directory)
    dist1, dist2, course1, course2, speed1, speed2, peleng1, peleng2, safe_diverg, speed = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    if len(split) > 0 and split[0] == 'sc':
        with open(os.path.join(case_directory + '/nav-data.json'), "r") as fp:
            nav_data = json.load(fp)
        with open(os.path.join(case_directory + '/target-data.json'), "r") as fp:
            targets_data = json.load(fp)
        with open(os.path.join(case_directory + '/settings.json'), "r") as fp:
            settings_data = json.load(fp)
        lat, lon = nav_data['lat'], nav_data['lon']
        safe_diverg = settings_data['maneuver_calculation']['safe_diverg_dist']
        speed = nav_data['SOG']

        if len(targets_data) < 3:
            for i, target in enumerate(targets_data):
                path = Geodesic.WGS84.Inverse(lat, lon, target['lat'], target['lon'])
                peleng = path['azi1']
                dist = path['s12'] / 1852
                if i == 0:
                    dist1 = dist
                    course1 = target["COG"]
                    peleng1 = peleng
                    speed1 = target["SOG"]
                if i == 1:
                    dist2 = dist
                    course2 = target["COG"]
                    peleng2 = peleng
                    speed2 = target["SOG"]

    case = PDCase(datadir, dist1, dist2, course1, course2, speed1, speed2, peleng1, peleng2, safe_diverg, speed)
    return case


def generate_metadata(data_directory, glob='*'):
    cases = []

    for path in Path(data_directory).glob(glob):
        for root, dirs, files in os.walk(path):
            if "nav-data.json" in files or 'navigation.json' in files:
                cases.append(get_metadata(root))
    df = pd.DataFrame(cases)
    df['datadir'] = [os.path.relpath(x, data_directory) for x in df['datadir']]
    df.to_csv(data_directory + '/metainfo.csv', float_format='%.13f')
    return df


class Generator(object):
    def __init__(self, safe_div_dist, lat=56.6857, lon=19.632):
        self.danger_points = []
        self.boost = int(1e2)
        self.our_vel = 0
        self.sdd = safe_div_dist
        self.frame = Frame(lat, lon)
        self.t2_folder = None
        self.abs_t2_folder = None
        self.abs_foldername = None
        self.dirlist = None
        self.cwd = os.getcwd()

    def construct_files(self, f_name, targets):
        """
        Constructs all json files
        @param f_name:
        @param targets:
        @return:
        """
        os.makedirs(f_name, exist_ok=True)
        with open(f_name + '/constraints.json', "w") as fp:
            json.dump(self.construct_constrains(), fp)
        with open(f_name + '/hmi-data.json', "w") as fp:
            json.dump(self.construct_hmi_data(), fp)
        with open(f_name + '/nav-data.json', "w") as fp:
            json.dump(self.construct_nav_data(), fp)
        with open(f_name + '/route-data.json', "w") as fp:
            json.dump(self.construct_route_data(), fp)
        with open(f_name + '/settings.json', "w") as fp:
            json.dump(self.construct_settings(), fp)
        with open(f_name + '/target-data.json', "w") as fp:
            json.dump(self.construct_target_data(targets), fp)
        with open(f_name + '/target-settings.json', "w") as fp:
            json.dump(self.construct_target_settings(), fp)

    def construct_target_data(self, targets):
        t_data = []
        for i, target in enumerate(targets):
            lat, lon = self.frame.to_wgs_azi(target['peleng'], target['dist'])
            payload = {
                "id": "target" + str(i),
                "cat": 0,
                "lat": lat,
                "lon": lon,
                "SOG": target['v_target'],
                "COG": target['c_diff'],
                "heading": target['c_diff'],
                "peleng": target['peleng'],
                "first_detect_dist": 5.0,
                "cross_dist": 0,
                "width": 16.0,
                "length": 100.0,
                "width_offset": 10.0,
                "length_offset": 15.0,
                "timestamp": 1594730134
            }
            t_data.append(payload)
        return t_data

    @staticmethod
    def construct_constrains():
        payload = {
            "type": "FeatureCollection",
            "features": []
        }
        return payload

    @staticmethod
    def construct_hmi_data():
        payload = {
            "wind_direction": 189.0,
            "wind_speed": 1.1,
            "tide_direction": 0.0,
            "tide_speed": 0.0,
            "swell": 1.0,
            "visibility": 13.0
        }
        return payload

    def construct_nav_data(self):
        payload = {
            "cat": 0,
            "lat": self.frame.lat,
            "lon": self.frame.lon,
            "SOG": self.our_vel,
            "STW": self.our_vel,
            "COG": 0.0,
            "heading": 0.0,
            "width": 16.0,
            "length": 100.0,
            "width_offset": 10.0,
            "length_offset": 15.0,
            "timestamp": 1594730134
        }
        return payload

    def construct_route_data(self):
        payload = {
            "items": [
                {
                    "begin_angle": 0.0,
                    "curve": 0,
                    "duration": 120.0 / self.our_vel * 3600,
                    "lat": self.frame.lat,
                    "lon": self.frame.lon,
                    "length": 120.0,
                    "port_dev": 1.5,
                    "starboard_dev": 1.5,
                }
            ],
            "start_time": 1594730134
        }
        return payload

    def construct_settings(self):
        payload = {
            "maneuver_calculation": {
                "priority": 0,
                "maneuver_way": 0,
                "safe_diverg_dist": self.sdd,
                "minimal_speed": 3.0,
                "maximal_speed": 30.0,
                "max_course_delta": 180,
                "time_advance": 300,
                "can_leave_route": True,
                "max_route_deviation": 4,
                "forward_speed1": 3.0,
                "forward_speed2": 9.75,
                "forward_speed3": 16.5,
                "forward_speed4": 23.25,
                "forward_speed5": 30.0,
                "reverse_speed1": 15.0,
                "reverse_speed2": 30.0,
                "max_circulation_radius": 0.3,
                "min_circulation_radius": 0.3,
                "breaking_distance": 0,
                "run_out_distance": 0,
                "forecast_time": 14400,
                "min_diverg_dist": 1.8
            },
            "safety_control": {
                "cpa": 2.0,
                "tcpa": 900,
                "min_detect_dist": 9.0,
                "last_moment_dist": 2.0,
                "safety_zone": {
                    "safety_zone_type": 0,
                    "radius": 1.0
                }
            }
        }
        return payload

    def construct_target_settings(self):
        payload = {
            "maneuver_calculation": {
                "priority": 0,
                "maneuver_way": 2,
                "safe_diverg_dist": self.sdd,
                "minimal_speed": 3.0,
                "maximal_speed": 30.0,
                "max_course_delta": 180,
                "time_advance": 300,
                "can_leave_route": True,
                "max_route_deviation": 8,
                "forward_speed1": 3.0,
                "forward_speed2": 9.75,
                "forward_speed3": 16.5,
                "forward_speed4": 23.25,
                "forward_speed5": 30.0,
                "reverse_speed1": 15.0,
                "reverse_speed2": 30.0,
                "max_circulation_radius": 0.1,
                "min_circulation_radius": 0.1,
                "breaking_distance": 0,
                "run_out_distance": 0,
                "forecast_time": 14400,
            },
            "safety_control": {
                "cpa": 2.0,
                "tcpa": 900,
                "min_detect_dist": 9.0,
                "last_moment_dist": 2.0,
                "safety_zone": {
                    "safety_zone_type": 0,
                    "radius": 1.0
                }
            }
        }
        return payload
