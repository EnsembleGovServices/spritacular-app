# Generated by Django 4.0.2 on 2022-03-10 09:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_alter_camerasetting_aperture'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserCountryFlag',
            fields=[
                ('id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True, null=True)),
                ('country', models.CharField(max_length=50)),
                ('code', models.CharField(max_length=10)),
                ('flag', models.ImageField(upload_to='country_flags')),
            ],
            options={
                'db_table': 'user_country_flag',
            },
        ),
        migrations.AddField(
            model_name='user',
            name='country_code',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='location',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]