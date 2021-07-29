import datetime
import os
import uuid

import pandas as pd
from django.db import models
from django.utils.text import slugify

from autotest import settings
from .build_graphs import build_percent_diag
from .decorators import postpone
from .generator import Generator


class TestingRecording(models.Model):
    date = models.DateTimeField(default=datetime.datetime.now)
    file = models.FileField(upload_to='')
    title = models.TextField(default="", max_length=1000)
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
    img_stats = models.ImageField(blank=True, upload_to='images')
    img_minister = models.ImageField(blank=True, upload_to='images')

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title + ' ' + str(self.date) + str(self.n_targets) + uuid.uuid4().hex[:6].upper())
        super().save(*args, **kwargs)
        if not self.processed:
            process_graphs(self)
            create_sc_for_rec(self)

    def __str__(self):
        return self.title + '_' + str(self.date)


@postpone
def process_graphs(recording):
    codes = build_percent_diag(recording.file.path, 12, 4, 0.5)
    recording.code0 = process_array(codes[0])
    recording.code1 = process_array(codes[1])
    recording.code2 = process_array(codes[2])
    recording.code4 = process_array(codes[3])
    recording.code5 = process_array(codes[4])
    recording.dists = process_array(codes[5])
    recording.n_targets = codes[6]
    recording.img_stats.name = codes[7]
    recording.img_minister.name = codes[8]
    # filename = os.path.splitext(os.path.split(recording.file.path)[1])[0]
    recording.date = datetime.datetime.now()
    recording.processed = True
    recording.save()


@postpone
def create_sc_for_rec(recording):
    df = None
    try:
        df = pd.read_excel(recording.file.path, engine='openpyxl')
    except:
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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        df = pd.read_csv(self.metafile.path)
        self.n_cases = len(df['datadirs'])
        for name in df['datadirs']:
            obj = Scenario()
            obj.name = os.path.split(name)[1]
            obj.scenariosSet = self
            obj.save()
        super().save(*args, **kwargs)


class Scenario(models.Model):
    name = models.TextField(blank=True, default='', max_length=500)
    num_targets = models.IntegerField(default=1)
    dist1 = models.FloatField(default=0)
    dist2 = models.FloatField(default=0)
    vel1 = models.FloatField(default=0)
    vel2 = models.FloatField(default=0)
    vel_our = models.FloatField(default=0)
    course1 = models.FloatField(default=0)
    course2 = models.FloatField(default=0)
    peleng1 = models.FloatField(default=0)
    peleng2 = models.FloatField(default=0)
    scenariosSet = models.ForeignKey(ScenariosSet, on_delete=models.CASCADE, default=1)

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
            names = self.name.split(sep='_')
            self.dist1 = names[1]
            self.dist2 = names[2]
            self.vel1 = names[3]
            self.vel2 = names[4]
            self.vel_our = names[5]
            self.course1 = names[6]
            self.course2 = names[7]
            if self.vel2 == self.course2 == 0:
                self.num_targets = 1
            else:
                self.num_targets = 2
        except IndexError:
            pass
        super().save(*args, **kwargs)

    def generate_folder(self, foldername=None):
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


class ComparationObject(models.Model):
    obj1 = models.ForeignKey(TestingRecording, on_delete=models.CASCADE, related_name='obj1')
    obj2 = models.ForeignKey(TestingRecording, on_delete=models.CASCADE, related_name='obj2')
    code0 = models.TextField(blank=True, default='', max_length=2000)
    code1 = models.TextField(blank=True, default='', max_length=2000)
    code2 = models.TextField(blank=True, default='', max_length=2000)
    code4 = models.TextField(blank=True, default='', max_length=2000)
    code5 = models.TextField(blank=True, default='', max_length=2000)
    n_targets = models.IntegerField(default=1)
    dists = models.TextField(blank=True, default='', max_length=2000)
    slug = models.SlugField(max_length=200, unique=True, default='')
    title = models.TextField(default="", max_length=1000)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.obj1.title + '_' + self.obj2.title + '_' + uuid.uuid4().hex[:6].upper())
        self.dists = self.obj1.dists
        self.title = "Сравнение кейса <" + self.obj1.title + "> с <" + self.obj2.title + ">"
        f = lambda s: [float(x) for x in s.split(sep='::')]
        code0_1 = f(self.obj1.code0)
        code1_1 = f(self.obj1.code1)
        code2_1 = f(self.obj1.code2)
        code4_1 = f(self.obj1.code4)
        code5_1 = f(self.obj1.code5)
        code0_2 = f(self.obj2.code0)
        code1_2 = f(self.obj2.code1)
        code2_2 = f(self.obj2.code2)
        code4_2 = f(self.obj2.code4)
        code5_2 = f(self.obj2.code5)
        for i in range(len(code0_1)):
            if i != len(code0_1) - 1:
                self.code0 += str(code0_2[i] - code0_1[i]) + "::"
                self.code1 += str(code1_2[i] - code1_1[i]) + "::"
                self.code2 += str(code2_2[i] - code2_1[i]) + "::"
                self.code4 += str(code4_2[i] - code4_1[i]) + "::"
                self.code5 += str(code5_2[i] - code5_1[i]) + "::"
            else:
                self.code0 += str(code0_2[i] - code0_1[i])
                self.code1 += str(code1_2[i] - code1_1[i])
                self.code2 += str(code2_2[i] - code2_1[i])
                self.code4 += str(code4_2[i] - code4_1[i])
                self.code5 += str(code5_2[i] - code5_1[i])
        super().save(*args, **kwargs)
