# Generated by Django 3.2.8 on 2021-11-26 13:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diagnosis', '0020_auto_20211019_1234'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='testingrecording',
            name='code0',
        ),
        migrations.RemoveField(
            model_name='testingrecording',
            name='code1',
        ),
        migrations.RemoveField(
            model_name='testingrecording',
            name='code2',
        ),
        migrations.RemoveField(
            model_name='testingrecording',
            name='code4',
        ),
        migrations.RemoveField(
            model_name='testingrecording',
            name='code5',
        ),
        migrations.RemoveField(
            model_name='testingrecording',
            name='dists',
        ),
        migrations.AlterField(
            model_name='testingrecording',
            name='commit_date',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
    ]