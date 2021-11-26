import os
import uuid

import iso8601
import pandas as pd
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from .build_graphs import plot_graph_normal, plot_minister_mode
from .decorators import postpone
from .gitgub_utils import get_commit


class TestingRecording(models.Model):
    date = models.DateTimeField(default=timezone.now)
    file = models.FileField(upload_to='')
    title = models.TextField(default="", max_length=1000)
    commit_sha1 = models.TextField(default="", max_length=40)
    commit_date = models.DateTimeField(default=None, null=True, blank=True)
    build_number = models.TextField(default="", max_length=20)
    n_targets = models.IntegerField(default=1)
    processed = models.BooleanField(default=False)
    slug = models.SlugField(max_length=200, unique=True, default='')
    n_scenarios = models.IntegerField(default=0)
    sc_set = models.ForeignKey("ScenariosSet", on_delete=models.CASCADE, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title + ' ' + str(self.date) + str(self.n_targets) + uuid.uuid4().hex[:6].upper())
        super().save(*args, **kwargs)
        if not self.processed:
            self.process_sha1()
            create_sc_for_rec(self)
            self.processed = True
            self.save()

    def process_sha1(self):
        if self.commit_sha1 and not self.title:
            commit = get_commit(repo_url=os.getenv('GITHUB_REPO_URL'), commit_sha1=self.commit_sha1,
                                token=os.getenv('GITHUB_TOKEN'))
            if commit is not None:
                self.title = commit['commit']['message']
                self.commit_date = iso8601.parse_date(commit['commit']['author']['date'])
            else:
                self.title = "Couldn't retrieve commit message"

    def pivot_scenario_types(self):
        """
        Calculates pivot table for code percentage per scenario type
        @rtype: pd.DataFrame
        """
        df = load_df_from_rec(self)
        if df is not None:
            a = df.melt(id_vars=df.columns[:-2], value_name="type").dropna(subset=["type"]).drop(columns=["variable"])
            p = pd.pivot_table(a, values='datadir', index=['type'], columns=['code'], aggfunc='count', fill_value=0)
            p_sum = p.sum(axis=1)
            return p.divide(p_sum, axis=0) * 100
        else:
            return None

    def to_dataframe(self):
        """
        Builds percent diagram with codes and errors to velocities graph
        @return: pd.Dataframe
        """
        filename = self.file.path

        try:
            file_extension = filename.split('.')[-1]
            if file_extension == 'parquet':
                df = pd.read_parquet(filename, engine='fastparquet')
            elif file_extension == 'xlsx':
                df = pd.read_excel(filename, engine='openpyxl')
            else:
                df = pd.read_csv(filename.path)
        except ValueError:
            df = pd.read_csv(filename.path)

        def get_distance(foldername):
            def get_n_targets(name):
                """
                Detects number of targets in case
                @param name: foldername with path
                @return:
                """
                foldername = os.path.split(name)[1]
                foldername2 = foldername.split(sep="_")
                if float(foldername2[1]) == 0 or float(foldername2[2]) == 0:
                    return 1
                else:
                    return 2

            foldername = os.path.split(foldername)[1]
            n_targ = get_n_targets(foldername)
            foldername2 = foldername.split(sep="_")
            if n_targ == 1:
                return max(float(foldername2[1]), float(foldername2[2]))
            elif n_targ == 2:
                return min(float(foldername2[1]), float(foldername2[2]))

        df['dist'] = df['datadir'].apply(get_distance)
        n_targ = 2 if len(df.query('dist1!=0 & dist2 != 0')) else 1
        a = pd.pivot_table(df, values='datadir', index=['dist'], columns=['code'], aggfunc='count', fill_value=0)
        asum = a.sum(axis=1)
        a = a.divide(asum, axis=0) * 100
        # a = a.set_index('dist')
        return a

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

    def gen_plot(self, graph_type='normal'):
        """
        Строит график по статистике записи тестирования
        @param graph_type: Тип графика: 'normal' или 'minister'
        @return: График
        """
        if graph_type == 'minister':
            return plot_minister_mode(self.to_dataframe(),
                                      title=f"Дата`{self.date}`. Целей: {self.n_targets}")
        else:
            return plot_graph_normal(self.to_dataframe(),
                                     title=f"`{self.title}`. Целей: {self.n_targets}")

    def __str__(self):
        return self.title + '_' + str(self.date)


def load_df_from_rec(recording):
    """
    Loads pandas df from recording stats file
    @param recording:
    @return:
    """
    try:
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

        return df
    except FileNotFoundError:
        return None


@postpone
def create_sc_for_rec(recording):
    df = load_df_from_rec(recording)

    i = 0
    for index, row in df.iterrows():
        i += 1
        try:
            scenario = Scenario.objects.get(name=os.path.split(row['datadir'])[1])
            obj = ScenarioResult()
            obj.scenario = scenario
            if i < 3:
                recording.sc_set = scenario.scenariosSet
                recording.save()
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
    dists = ArrayField(models.FloatField(), default=list)
    vels = ArrayField(models.FloatField(), default=list)
    vel_our = models.FloatField(default=0)
    courses = ArrayField(models.FloatField(), default=list)
    pelengs = ArrayField(models.FloatField(), default=list)
    scenariosSet = models.ForeignKey(ScenariosSet, on_delete=models.CASCADE, default=1)
    type = models.IntegerField(choices=TSS, default=0)

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
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
