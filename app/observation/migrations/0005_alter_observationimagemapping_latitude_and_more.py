# Generated by Django 4.0.2 on 2022-03-09 06:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observation', '0004_observationimagemapping_is_precise_azimuth_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='observationimagemapping',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=16, max_digits=22, null=True),
        ),
        migrations.AlterField(
            model_name='observationimagemapping',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=16, max_digits=22, null=True),
        ),
    ]
