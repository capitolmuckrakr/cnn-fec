# Generated by Django 2.0.1 on 2018-07-13 18:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cycle_2018', '0025_auto_20180713_1742'),
    ]

    operations = [
        migrations.AddField(
            model_name='donor',
            name='contribution_total',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
    ]