# Generated by Django 3.2.7 on 2021-09-08 13:19
import re
import iso8601

from django.db import migrations, models


def split_commit_sha_and_date(apps, schema_editor):
    Record = apps.get_model('diagnosis', 'TestingRecording')
    records = Record.objects.all().iterator()
    regex = re.compile(r"(.+)\s([0-9a-f]{7})\s-\s(.+)")

    for record in records:
        m = regex.match(record.title)
        if m is not None:
            record.commit_sha1 = m.group(2)
            record.commit_date = iso8601.parse_date(m.group(1))
            record.title = m.group(3)

            record.save()


class Migration(migrations.Migration):
    dependencies = [
        ('diagnosis', '0016_auto_20210816_0007'),
    ]

    operations = [
        migrations.AddField(
            model_name='testingrecording',
            name='commit_date',
            field=models.DateTimeField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='testingrecording',
            name='commit_sha1',
            field=models.TextField(default='', max_length=40),
        ),
        migrations.RunPython(split_commit_sha_and_date)
    ]
