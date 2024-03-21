# Generated by Django 5.0.2 on 2024-03-18 15:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0011_alter_room_current_player'),
    ]

    operations = [
        migrations.AddField(
            model_name='charactercard',
            name='additional_info_hidden',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='charactercard',
            name='bio_hidden',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='charactercard',
            name='health_hidden',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='charactercard',
            name='hobby_hidden',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='charactercard',
            name='knowledge_hidden',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='charactercard',
            name='luggage_hidden',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='charactercard',
            name='phobia_hidden',
            field=models.BooleanField(default=True),
        ),
    ]