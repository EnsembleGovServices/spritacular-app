# Generated by Django 4.0.2 on 2022-02-27 10:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observation', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='observationimagemapping',
            name='obs_date_time_as_per_utc',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
