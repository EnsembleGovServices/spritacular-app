# Generated by Django 4.0.2 on 2022-04-19 09:02

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0015_alter_user_location_metadata'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='uid',
            field=models.UUIDField(default=uuid.uuid4),
        ),
    ]
