# Generated by Django 5.0.4 on 2024-04-11 11:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0020_room_turn_ended'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='voting_started',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='place',
            name='can_end_turn',
            field=models.BooleanField(default=True),
        ),
    ]