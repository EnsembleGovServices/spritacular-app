# Generated by Django 4.0.2 on 2022-04-12 07:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observation', '0011_observationimagemapping_image_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='observation',
            name='story',
            field=models.TextField(blank=True, default=''),
        ),
    ]
