# Generated by Django 3.2.13 on 2022-07-18 07:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0003_configuration'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='is_user_credit',
            field=models.BooleanField(default=False),
        ),
    ]
