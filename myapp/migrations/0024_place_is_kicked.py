# Generated by Django 5.0.4 on 2024-04-27 12:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0023_place_voted'),
    ]

    operations = [
        migrations.AddField(
            model_name='place',
            name='is_kicked',
            field=models.BooleanField(default=False),
        ),
    ]
