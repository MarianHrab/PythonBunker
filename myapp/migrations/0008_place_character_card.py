# Generated by Django 5.0.2 on 2024-03-15 09:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0007_remove_charactercard_bio_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='place',
            name='character_card',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='myapp.charactercard'),
        ),
    ]
