# Generated by Django 3.2.13 on 2022-07-05 07:04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('observation', '0012_alter_observation_story'),
    ]

    operations = [
        migrations.AddField(
            model_name='observation',
            name='verified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='verified_by', to=settings.AUTH_USER_MODEL),
        ),
    ]
