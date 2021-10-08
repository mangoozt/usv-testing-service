# Generated by Django 3.2.7 on 2021-10-08 14:00

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('diagnosis', '0017_auto_20210908_1619'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scenario',
            name='course1',
        ),
        migrations.RemoveField(
            model_name='scenario',
            name='course2',
        ),
        migrations.RemoveField(
            model_name='scenario',
            name='dist1',
        ),
        migrations.RemoveField(
            model_name='scenario',
            name='dist2',
        ),
        migrations.RemoveField(
            model_name='scenario',
            name='peleng1',
        ),
        migrations.RemoveField(
            model_name='scenario',
            name='peleng2',
        ),
        migrations.RemoveField(
            model_name='scenario',
            name='vel1',
        ),
        migrations.RemoveField(
            model_name='scenario',
            name='vel2',
        ),
        migrations.AddField(
            model_name='scenario',
            name='courses',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(), default=list, size=None),
        ),
        migrations.AddField(
            model_name='scenario',
            name='dists',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(), default=list, size=None),
        ),
        migrations.AddField(
            model_name='scenario',
            name='pelengs',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(), default=list, size=None),
        ),
        migrations.AddField(
            model_name='scenario',
            name='type',
            field=models.IntegerField(choices=[(0, 'Face to face'), (1, 'Overtaken'), (2, 'Overtake'), (3, 'Give way'), (4, 'Save'), (5, 'Give way priority'), (6, 'Save priority'), (7, 'Cross move'), (8, 'Cross in'), (9, 'Vision restricted forward'), (10, 'Vision restricted backward')], default=0),
        ),
        migrations.AddField(
            model_name='scenario',
            name='vels',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(), default=list, size=None),
        ),
        migrations.AddField(
            model_name='scenariosset',
            name='ci',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='scenariosset',
            name='cm',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='scenariosset',
            name='f2f',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='scenariosset',
            name='gw',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='scenariosset',
            name='gwp',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='scenariosset',
            name='ov',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='scenariosset',
            name='ovn',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='scenariosset',
            name='sp',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='scenariosset',
            name='sve',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='scenariosset',
            name='validation',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='scenariosset',
            name='vrb',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='scenariosset',
            name='vrf',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='testingrecording',
            name='ci',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='testingrecording',
            name='cm',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='testingrecording',
            name='f2f',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='testingrecording',
            name='gw',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='testingrecording',
            name='gwp',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='testingrecording',
            name='ov',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='testingrecording',
            name='ovn',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='testingrecording',
            name='sc_set',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='diagnosis.scenariosset'),
        ),
        migrations.AddField(
            model_name='testingrecording',
            name='sp',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='testingrecording',
            name='sve',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='testingrecording',
            name='vrb',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='testingrecording',
            name='vrf',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='testingrecording',
            name='date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
