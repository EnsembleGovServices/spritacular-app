# Generated by Django 3.2.13 on 2022-07-01 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0007_blogimagedata_blog'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContentManagement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.TextField(default='')),
                ('content', models.TextField(default='')),
            ],
        ),
    ]