# Generated by Django 2.0.1 on 2018-07-13 17:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cycle_2018', '0024_filingstatus'),
    ]

    operations = [
        migrations.AddField(
            model_name='donor',
            name='city',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='donor',
            name='state',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]