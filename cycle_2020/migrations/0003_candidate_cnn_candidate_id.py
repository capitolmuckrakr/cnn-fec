# Generated by Django 2.2 on 2019-05-13 21:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cycle_2020', '0002_triggers'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidate',
            name='cnn_candidate_id',
            field=models.CharField(blank=True, max_length=9, null=True),
        ),
    ]
