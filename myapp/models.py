from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Room(models.Model):
    name = models.CharField(max_length=100)
    max_players = models.IntegerField()
    password = models.CharField(max_length=100, blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    game_started = models.BooleanField(default=False)  # Додали поле для відстеження стану гри

    def __str__(self):
        return self.name


class Place(models.Model):
    room = models.ForeignKey('Room', on_delete=models.CASCADE)
    player_name = models.CharField(max_length=100, blank=True, null=True)

class CharacterCard(models.Model):
    player = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    health = models.CharField(blank=True, max_length=100)
    phobia = models.CharField(blank=True, max_length=100)
    hobby = models.CharField(blank=True, max_length=100)
    knowledge = models.CharField(blank=True, max_length=100)
    additional_info = models.TextField(blank=True)
    luggage = models.TextField(blank=True)

    # Додайте поля для зберігання варіантів для кожної характеристики
    BIO_OPTIONS = (
        ('option1', 'Option 1'),
        ('option2', 'Option 2'),
        # Додайте інші варіанти для bio
    )
    HEALTH_OPTIONS = (
        ('option1', 'Option 1'),
        ('option2', 'Option 2'),
        # Додайте інші варіанти для health
    )
    PHOBIA_OPTIONS = (
        ('option1', 'Option 1'),
        ('option2', 'Option 2'),
        # Додайте інші варіанти для phobia
    )
    HOBBY_OPTIONS = (
        ('option1', 'Option 1'),
        ('option2', 'Option 2'),
        # Додайте інші варіанти для phobia
    )
    KNOWLEDGE_OPTIONS = (
        ('option1', 'Option 1'),
        ('option2', 'Option 2'),
        # Додайте інші варіанти для phobia
    )
    ADDITIONAL_INFO_OPTIONS = (
        ('option1', 'Option 1'),
        ('option2', 'Option 2'),
        # Додайте інші варіанти для phobia
    )
    LUGGAGE_OPTIONS = (
        ('option1', 'Option 1'),
        ('option2', 'Option 2'),
        # Додайте інші варіанти для phobia
    )
    # Додайте інші варіанти для phobia
    # Додайте інші поля з варіантами для інших характеристик, які вам потрібні

    def __str__(self):
        return f'Character Card for {self.player.username}'