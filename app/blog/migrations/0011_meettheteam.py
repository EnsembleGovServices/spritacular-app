# Generated by Django 3.2.13 on 2022-08-22 06:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0010_alter_contentmanagement_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='MeetTheTeam',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('url', models.URLField(blank=True, null=True)),
                ('organization', models.CharField(max_length=200)),
                ('role', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('image', models.ImageField(upload_to='spritacular_team')),
            ],
        ),
    ]
