# Generated by Django 3.2.5 on 2021-07-22 13:30

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('diagnosis', '0002_testingrecording_dists'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testingrecording',
            name='file',
            field=models.FileField(upload_to=''),
        ),
    ]
