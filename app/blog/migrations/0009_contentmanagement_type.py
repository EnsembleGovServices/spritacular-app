# Generated by Django 3.2.13 on 2022-07-01 13:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0008_contentmanagement'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentmanagement',
            name='type',
            field=models.CharField(choices=[('policy', 'Spritacular Policy'), ('become_an_ambassador', 'Become an ambassador'), ('spritacular_google_group', 'Spritacular Google Group')], default='policy', max_length=100),
            preserve_default=False,
        ),
    ]
