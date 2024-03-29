# Generated by Django 3.2.13 on 2022-07-29 11:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observation', '0015_observation_media_file_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='observation',
            name='image_type',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Single image'), (3, 'Images sequence from video recorded.')], default=1),
        ),
        migrations.AlterField(
            model_name='observationreasonforreject',
            name='additional_comment',
            field=models.TextField(blank=True, default=''),
        ),
    ]
