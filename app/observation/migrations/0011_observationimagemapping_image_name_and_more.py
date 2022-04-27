# Generated by Django 4.0.2 on 2022-04-08 06:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observation', '0010_observationreasonforreject'),
    ]

    operations = [
        migrations.AddField(
            model_name='observationimagemapping',
            name='image_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='observationimagemapping',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='observation_image'),
        ),
    ]
