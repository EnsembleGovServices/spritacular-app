# Generated by Django 4.0.2 on 2022-04-06 09:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('observation', '0009_observationwatchcount'),
    ]

    operations = [
        migrations.CreateModel(
            name='ObservationReasonForReject',
            fields=[
                ('id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True, null=True)),
                ('additional_comment', models.CharField(blank=True, max_length=200, null=True)),
                ('inappropriate_image', models.BooleanField(default=False)),
                ('other', models.BooleanField(default=False)),
                ('observation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='observation.observation')),
            ],
            options={
                'db_table': 'observation_reason_for_reject',
            },
        ),
    ]
