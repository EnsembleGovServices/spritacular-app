# Generated by Django 4.0.2 on 2022-02-18 10:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_user_uid'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_first_login',
            field=models.BooleanField(default=False),
        ),
    ]
