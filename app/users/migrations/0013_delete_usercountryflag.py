# Generated by Django 4.0.2 on 2022-03-11 08:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0012_user_place_uid'),
    ]

    operations = [
        migrations.DeleteModel(
            name='UserCountryFlag',
        ),
    ]