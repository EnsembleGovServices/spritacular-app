# Generated by Django 3.2.13 on 2022-05-19 11:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='quizattempt',
            name='question_data',
            field=models.JSONField(default=dict),
        ),
    ]
