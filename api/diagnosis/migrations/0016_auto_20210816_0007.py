# Generated by Django 3.2.5 on 2021-08-15 21:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('diagnosis', '0015_delete_comparationobject'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='testingrecording',
            name='img_minister',
        ),
        migrations.RemoveField(
            model_name='testingrecording',
            name='img_stats',
        ),
    ]
