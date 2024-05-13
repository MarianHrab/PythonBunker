from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from .utils import BIO_OPTIONS, HEALTH_OPTIONS, PHOBIA_OPTIONS, HOBBY_OPTIONS, KNOWLEDGE_OPTIONS, \
    ADDITIONAL_INFO_OPTIONS, LUGGAGE_OPTIONS
from django.db.models.signals import pre_delete
from django.dispatch import receiver


class Room(models.Model):
    initial_players_count = models.PositiveIntegerField(default=0)
    name = models.CharField(max_length=100)
    char_by_turn = models.IntegerField(default=1)
    max_players = models.IntegerField()
    password = models.CharField(max_length=100, blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rooms')
    current_player = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='current_player_rooms')
    game_started = models.BooleanField(default=False)
    current_turn_player = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                            related_name='current_turn_player_rooms')
    turn_ended = models.BooleanField(default=False)
    voting_started = models.BooleanField(default=False)
    game_finished = models.BooleanField(default=False)

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
    characteristic_opened = models.BooleanField(default=False)
    player = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    health = models.CharField(blank=True, max_length=100)
    phobia = models.CharField(blank=True, max_length=100)
    hobby = models.CharField(blank=True, max_length=100)
    knowledge = models.CharField(blank=True, max_length=100)
    additional_info = models.TextField(blank=True)
    luggage = models.TextField(blank=True)

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
    can_end_turn = models.BooleanField(default=True)
    voted = models.BooleanField(default=False)
    is_kicked = models.BooleanField(default=False)

    def __str__(self):
        return f'Character Card for {self.player_name}'


class Vote(models.Model):
    voter = models.ForeignKey(User, on_delete=models.CASCADE)  # Гравець, який голосує
    target_player = models.ForeignKey(User, on_delete=models.CASCADE,
                                      related_name='received_votes')  # Гравець, на якого голосують
    room = models.ForeignKey(Room, on_delete=models.CASCADE)  # Кімната, де відбувається голосування
    created_at = models.DateTimeField(auto_now_add=True)  # Дата та час створення голосу

    def __str__(self):
        return f"Vote from {self.voter.username} to {self.target_player.username} in room {self.room.id}"
