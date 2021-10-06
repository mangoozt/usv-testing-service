import os
import uuid

import pandas as pd
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from autotest import settings
from .build_graphs import build_percent_diag, plot_graph_normal, plot_minister_mode
from .decorators import postpone
from .generator import Generator


class TestingRecording(models.Model):
    date = models.DateTimeField(default=timezone.now())
    file = models.FileField(upload_to='')
    title = models.TextField(default="", max_length=1000)
    commit_sha1 = models.TextField(default="", max_length=40)
    commit_date = models.DateTimeField(default=None, null=True)
    # We will storage all plots data in string format using '::' delimiter
    code0 = models.TextField(blank=True, default='', max_length=2000)
    code1 = models.TextField(blank=True, default='', max_length=2000)
    code2 = models.TextField(blank=True, default='', max_length=2000)
    code4 = models.TextField(blank=True, default='', max_length=2000)
    code5 = models.TextField(blank=True, default='', max_length=2000)
    n_targets = models.IntegerField(default=1)
    dists = models.TextField(blank=True, default='', max_length=2000)
    processed = models.BooleanField(default=False)
    slug = models.SlugField(max_length=200, unique=True, default='')
    n_scenarios = models.IntegerField(default=0)
    f2f = models.IntegerField(default=0)
    ovn = models.IntegerField(default=0)
    ov = models.IntegerField(default=0)
    gw = models.IntegerField(default=0)
    sve = models.IntegerField(default=0)
    gwp = models.IntegerField(default=0)
    sp = models.IntegerField(default=0)
    cm = models.IntegerField(default=0)
    ci = models.IntegerField(default=0)
    vrf = models.IntegerField(default=0)
    vrb = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title + ' ' + str(self.date) + str(self.n_targets) + uuid.uuid4().hex[:6].upper())
        super().save(*args, **kwargs)
        if not self.processed:
            process_graphs(self)
            create_sc_for_rec(self)

    def to_dataframe(obj):
        def f(arr):
            return [float(a) for a in arr.split(sep='::')]

        return pd.DataFrame(
            data=list(zip(f(obj.dists), f(obj.code0), f(obj.code1), f(obj.code2), f(obj.code4), f(obj.code5))),
            columns=('Дистанция', 'Код 0', 'Код 1', 'Код 2', 'Код 4', 'Код 5')).set_index('Дистанция')

    def compare(self, previous):
        """
        Compares testing record to another. Value from other record subtracted from this record values
        @param previous:
        @type previous: TestingRecording
        @rtype: pd.DataFrame
        """

        self_chart_data = self.to_dataframe()
        previous_chart_data = previous.to_dataframe()

        result = self_chart_data.sub(previous_chart_data)

        return result

    def gen_plot(self, type='normal'):
        """
        Строит график по статистике записи тестирования
        @param type: Тип графика: 'normal' или 'minister'
        @return: График
        """
        if type == 'minister':
            return plot_minister_mode(self.to_dataframe(),
                                      title=f"Дата`{self.date}`. Целей: {self.n_targets}")
        else:
            return plot_graph_normal(self.to_dataframe(),
                                     title=f"`{self.title}`. Целей: {self.n_targets}")

    def __str__(self):
        return self.title + '_' + str(self.date)


@postpone
def process_graphs(recording):
    codes = build_percent_diag(recording.file.path)
    recording.code0 = process_array(codes[0])
    recording.code1 = process_array(codes[1])
    recording.code2 = process_array(codes[2])
    recording.code4 = process_array(codes[3])
    recording.code5 = process_array(codes[4])
    recording.dists = process_array(codes[5])
    recording.n_targets = codes[6]
    recording.date = timezone.now()
    recording.processed = True
    recording.save()


@postpone
def create_sc_for_rec(recording):
    try:
        file_extension = recording.file.path.split('.')[-1]
        if file_extension == 'parquet':
            df = pd.read_parquet(recording.file.path)
        elif file_extension == 'xlsx':
            df = pd.read_excel(recording.file.path, engine='openpyxl')
        else:
            df = pd.read_csv(recording.file.path)
    except ValueError:
        df = pd.read_csv(recording.file.path)

    i = 0
    for index, row in df.iterrows():
        i += 1
        try:
            scenario = Scenario.objects.get(name=os.path.split(row['datadir'])[1])
            obj = ScenarioResult()
            obj.scenario = scenario
            obj.pack = recording
            obj.code = row['code']
            obj.exec_time = row['exec_time']
            obj.nav_report = row['nav_report']
            obj.command = row['command']
            obj.dist1 = row['dist1']
            obj.dist2 = row['dist2']
            obj.course1 = row['course1']
            obj.course2 = row['course2']
            obj.peleng1 = row['peleng1']
            obj.peleng2 = row['peleng2']
            obj.type1 = row['type1']
            obj.type2 = row['type2']
            obj.save()
        except:
            continue
    recording.n_scenarios = i
    recording.save()


def process_array(arr):
    s = ""
    for i, a in enumerate(arr):
        s += str(a)
        if i != len(arr) - 1:
            s += "::"
    return s


class ScenariosSet(models.Model):
    n_targets = models.IntegerField(default=1)
    n_cases = models.IntegerField(default=0)
    metafile = models.FileField(upload_to='', blank=True)
    validation = models.BooleanField(default=False)
    # Scenario types
    f2f = models.IntegerField(default=0)
    ovn = models.IntegerField(default=0)
    ov = models.IntegerField(default=0)
    gw = models.IntegerField(default=0)
    sve = models.IntegerField(default=0)
    gwp = models.IntegerField(default=0)
    sp = models.IntegerField(default=0)
    cm = models.IntegerField(default=0)
    ci = models.IntegerField(default=0)
    vrf = models.IntegerField(default=0)
    vrb = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        df = pd.read_csv(self.metafile.path)
        self.n_cases = len(df['datadirs'])
        for name in df['datadirs']:
            obj = Scenario()
            obj.name = os.path.split(name)[1]
            obj.scenariosSet = self
            # TODO: Fix types
            # obj.type = ...
            obj.save()
        self.f2f = len(df[df['type1'] == "Face to face"])
        self.ovn = len(df[df['type1'] == "Overtaken"])
        self.ov = len(df[df['type1'] == "Overtake"])
        self.gw = len(df[df['type1'] == "Give way"])
        self.sve = len(df[df['type1'] == "Save"])
        self.gwp = len(df[df['type1'] == "Give way priority"])
        self.sp = len(df[df['type1'] == "Save priority"])
        self.cm = len(df[df['type1'] == "Cross move"])
        self.ci = len(df[df['type1'] == "Cross in"])
        self.vrf = len(df[df['type1'] == "Vision restricted forward"])
        self.vrb = len(df[df['type1'] == "Vision restricted backward"])
        super().save(*args, **kwargs)


TSS = (
    (0, "Face to face"),
    (1, "Overtaken"),
    (2, "Overtake"),
    (3, "Give way"),
    (4, "Save"),
    (5, "Give way priority"),
    (6, "Save priority"),
    (7, "Cross move"),
    (8, "Cross in"),
    (9, "Vision restricted forward"),
    (10, "Vision restricted backward")
)


class Scenario(models.Model):
    name = models.TextField(blank=True, default='', max_length=500)
    num_targets = models.IntegerField(default=1)
    dists = ArrayField(models.FloatField(), default=[0])
    vels = ArrayField(models.FloatField(), default=[0])
    vel_our = models.FloatField(default=0)
    courses = ArrayField(models.FloatField(), default=[0])
    pelengs = ArrayField(models.FloatField(), default=[0])
    scenariosSet = models.ForeignKey(ScenariosSet, on_delete=models.CASCADE, default=1)
    type = models.IntegerField(choices=TSS, default=0)

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
            names = self.name.split(sep='_')
            # TODO: rewrite this shit to file reading
            # self.dist1 = names[1]
            # self.dist2 = names[2]
            # self.vel1 = names[3]
            # self.vel2 = names[4]
            # self.vel_our = names[5]
            # self.course1 = names[6]
            # self.course2 = names[7]
            # if self.vel2 == self.course2 == 0:
            #     self.num_targets = 1
            # else:
            #     self.num_targets = 2
        except IndexError:
            pass
        super().save(*args, **kwargs)

    def generate_folder(self, foldername=None):
        # TODO: rewrite this bullshit too
        gen = Generator(12, 3.5, 300, 1000, safe_div_dist=1, n_targets=1, foldername="./scenars_div1_1tar",
                        n_stack=1000)
        targets = []
        if self.dist1 != 0:
            targets.append({"course": self.course1,
                            "dist": self.dist1,
                            "c_diff": self.course1,
                            "v_our": self.vel_our,
                            "v_target": self.vel1})
        if self.dist2 != 0:
            targets.append({"course": self.course2,
                            "dist": self.dist2,
                            "c_diff": self.course2,
                            "v_our": self.vel_our,
                            "v_target": self.vel2})
        f_name = ("./sc_" + str(targets[0]['dist']) + str(self.pk))
        os.chdir(settings.BASE_DIR)
        gen.our_vel = self.vel_our
        gen.construct_files(f_name, targets)


STATUS = (
    (0, 'OK'),
    (1, 'Ok with violations'),
    (2, 'Not solved'),
    (3, 'Refuse: too many targets'),
    (4, 'Undefined scenario for dangerous target'),
    (5, 'No dangerous vehicles')
)


class ScenarioResult(models.Model):
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    pack = models.ForeignKey(TestingRecording, on_delete=models.CASCADE)
    code = models.IntegerField(choices=STATUS, default=0)
    exec_time = models.FloatField(default=0)
    nav_report = models.TextField(default='', max_length=3000)
    command = models.TextField(default='', max_length=3000)
    dist1 = models.FloatField(default=0)
    dist2 = models.FloatField(default=0)
    course1 = models.FloatField(default=0)
    course2 = models.FloatField(default=0)
    peleng1 = models.FloatField(default=0)
    peleng2 = models.FloatField(default=0)
    type1 = models.TextField(default='', max_length=300)
    type2 = models.TextField(default='', max_length=300)
