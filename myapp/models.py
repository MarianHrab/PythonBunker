from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from .utils import BIO_OPTIONS, HEALTH_OPTIONS, PHOBIA_OPTIONS, HOBBY_OPTIONS, KNOWLEDGE_OPTIONS, \
    ADDITIONAL_INFO_OPTIONS, LUGGAGE_OPTIONS

from django.db.models.signals import pre_delete
from django.dispatch import receiver


class Room(models.Model):
    name = models.CharField(max_length=100)
    max_players = models.IntegerField()
    password = models.CharField(max_length=100, blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rooms')
    current_player = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_player_rooms')
    game_started = models.BooleanField(default=False)
    current_turn_player = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_turn_player_rooms')

    def __str__(self):
        return self.name

@receiver(pre_delete, sender=Room)
def delete_character_cards(sender, instance, **kwargs):
    # Отримати всі місця для даної кімнати
    places = instance.place_set.all()

    # Отримати всі CharacterCard, які потрібно видалити
    character_cards = CharacterCard.objects.filter(place__room=instance)

    # Видалити всі знайдені CharacterCard
    character_cards.delete()

class CharacterCard(models.Model):
    player = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    health = models.CharField(blank=True, max_length=100)
    phobia = models.CharField(blank=True, max_length=100)
    hobby = models.CharField(blank=True, max_length=100)
    knowledge = models.CharField(blank=True, max_length=100)
    additional_info = models.TextField(blank=True)
    luggage = models.TextField(blank=True)

    # Додайте поля для статусу кожної характеристики
    bio_hidden = models.BooleanField(default=True)
    health_hidden = models.BooleanField(default=True)
    phobia_hidden = models.BooleanField(default=True)
    hobby_hidden = models.BooleanField(default=True)
    knowledge_hidden = models.BooleanField(default=True)
    additional_info_hidden = models.BooleanField(default=True)
    luggage_hidden = models.BooleanField(default=True)

    BIO_OPTIONS = BIO_OPTIONS
    HEALTH_OPTIONS = HEALTH_OPTIONS
    PHOBIA_OPTIONS = PHOBIA_OPTIONS
    HOBBY_OPTIONS = HOBBY_OPTIONS
    KNOWLEDGE_OPTIONS = KNOWLEDGE_OPTIONS
    ADDITIONAL_INFO_OPTIONS = ADDITIONAL_INFO_OPTIONS
    LUGGAGE_OPTIONS = LUGGAGE_OPTIONS

class Place(models.Model):
    room = models.ForeignKey('Room', on_delete=models.CASCADE)
    player_name = models.CharField(max_length=100, blank=True, null=True)
    character_card = models.ForeignKey('CharacterCard', on_delete=models.SET_NULL, null=True, blank=True)
    turn_finished = models.BooleanField(default=False)
    def __str__(self):
        return f'Character Card for {self.player_name}'


