from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from .models import Room, Place
from .forms import RoomForm
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from .models import Place, CharacterCard
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Room
import random
from django.db import transaction
from django.db.models import Min, F

from .utils import (
    BIO_OPTIONS,
    HEALTH_OPTIONS,
    PHOBIA_OPTIONS,
    KNOWLEDGE_OPTIONS,
    HOBBY_OPTIONS,
    ADDITIONAL_INFO_OPTIONS,
    LUGGAGE_OPTIONS,
)


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


def index(request):
    # Отримати всі кімнати
    rooms = Room.objects.all()

    # Якщо форму було надіслано
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.creator = request.user  # Зберігаємо користувача, який створив кімнату
            room.save()
            return redirect('index')  # Перенаправлення на головну сторінку
    else:
        form = RoomForm()

    # Передача кімнат та форми в контекст шаблону
    context = {
        'rooms': rooms,
        'form': form,
    }

    # Відображення шаблону
    return render(request, 'index.html', context)


def room_detail(request, room_id):
    # Отримати кімнату за ідентифікатором
    room = get_object_or_404(Room, id=room_id)

    # Отримати або створити місця для кімнати
    places = room.place_set.all()
    if not places:
        for i in range(room.max_players):
            place = Place.objects.create(room=room)
            places = room.place_set.all()  # Оновити список місць після створення нового місця

    # Отримати список гравців у кімнаті через модель Place
    players = [place.player_name for place in places if place.player_name]

    # Отримати об'єкти User для гравців у кімнаті
    player_users = User.objects.filter(username__in=players)

    return render(request, 'room_detail.html',
                  {'room': room, 'places': places, 'room_id': room_id, 'players': player_users})


def take_place(request, room_id, place_id):
    # Отримати кімнату за ідентифікатором
    room = get_object_or_404(Room, id=room_id)

    # Перевірка, чи користувач вже має місце в цій кімнаті
    existing_place = room.place_set.filter(player_name=request.user.username).first()
    if existing_place:
        # Звільнити його поточне місце
        existing_place.player_name = None
        existing_place.save()

    # Отримати місце за ідентифікатором
    place = get_object_or_404(Place, id=place_id, room=room)

    # Перевірка, чи місце вільне
    if place.player_name:
        return JsonResponse({'error': 'Place already taken'})

    # Займіть місце
    place.player_name = request.user.username
    place.save()

    return JsonResponse({'player_name': request.user.username})


@require_http_methods(["DELETE"])
def delete_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    if request.user == room.creator:
        room.delete()
        return HttpResponse(status=204)  # Код 204 означає успішне видалення
    else:
        return HttpResponse(status=403)  # Код 403 означає заборону доступу


@login_required
def start_game(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    # Отримуємо всі місця у кімнаті
    places = room.place_set.all()

    # Перевіряємо, чи користувач вже зайняв місце
    place = places.filter(player_name=request.user.username).first()
    if not place:
        return HttpResponse(status=403)  # Код 403 означає заборону доступу

    # Перевіряємо, чи гра вже стартувала
    if room.game_started:
        return HttpResponse("The game has already started")

    # Запускаємо гру
    room.game_started = True

    # Призначаємо поточного гравця як користувача, який ініціював запит
    room.current_turn_player = request.user

    # Зберігаємо зміни
    room.save()

    # Роздаємо характеристики гравцям
    with transaction.atomic():
        for place in places:
            if place.player_name:
                # Створюємо новий CharacterCard для кожного гравця
                character_card = CharacterCard.objects.create(
                    player=User.objects.get(username=place.player_name),
                    bio=random.choice(BIO_OPTIONS) if BIO_OPTIONS else '',
                    health=random.choice(HEALTH_OPTIONS) if HEALTH_OPTIONS else '',
                    phobia=random.choice(PHOBIA_OPTIONS) if PHOBIA_OPTIONS else '',
                    hobby=random.choice(HOBBY_OPTIONS) if HOBBY_OPTIONS else '',
                    knowledge=random.choice(KNOWLEDGE_OPTIONS) if KNOWLEDGE_OPTIONS else '',
                    additional_info=random.choice(ADDITIONAL_INFO_OPTIONS) if ADDITIONAL_INFO_OPTIONS else '',
                    luggage=random.choice(LUGGAGE_OPTIONS) if LUGGAGE_OPTIONS else '',
                )
                # Присвоюємо створену CharacterCard об'єкту місця
                place.character_card = character_card
                place.save()

    # Повертаємо відповідь JSON, що підтверджує успішний початок гри
    return JsonResponse({'message': 'Гра успішно розпочалася'})


def endTurn(request, room_id):
    # Отримати об'єкт кімнати за room_id
    room = get_object_or_404(Room, id=room_id)

    # Перевірка, чи гра взагалі розпочалася
    if not room.game_started:
        return JsonResponse({'error': 'Гра ще не розпочалася'}, status=400)

    # Отримати місце поточного гравця
    place = Place.objects.filter(room=room, player_name=request.user.username).first()

    # Перевірити, чи гравець перебуває в цій кімнаті
    if not place:
        return JsonResponse({'error': 'Ви не перебуваєте в цій кімнаті'}, status=400)

    # Позначити хід гравця як завершений
    place.turn_finished = True
    place.save()

    # Повернути підтвердження у форматі JSON
    return JsonResponse({'message': 'Хід завершено успішно'})


def character_info(request):
    user = request.user
    try:
        # Спробуйте отримати об'єкт CharacterCard для поточного користувача
        character_card = CharacterCard.objects.get(player=user)
    except CharacterCard.DoesNotExist:
        # Якщо об'єкт не існує, створіть його з випадковими значеннями
        bio = random.choice(BIO_OPTIONS) if BIO_OPTIONS else 'нема'
        health = random.choice(HEALTH_OPTIONS) if HEALTH_OPTIONS else 'нема'
        phobia = random.choice(PHOBIA_OPTIONS) if PHOBIA_OPTIONS else 'нема'
        hobby = random.choice(HOBBY_OPTIONS) if HOBBY_OPTIONS else 'нема'
        knowledge = random.choice(KNOWLEDGE_OPTIONS) if KNOWLEDGE_OPTIONS else 'нема'
        additional_info = random.choice(ADDITIONAL_INFO_OPTIONS) if ADDITIONAL_INFO_OPTIONS else 'нема'
        luggage = random.choice(LUGGAGE_OPTIONS) if LUGGAGE_OPTIONS else 'нема'

        character_card = CharacterCard.objects.create(
            player=user,
            bio=bio,
            health=health,
            phobia=phobia,
            hobby=hobby,
            knowledge=knowledge,
            additional_info=additional_info,
            luggage=luggage
        )

    return render(request, 'character_info.html', {'character_card': character_card})


@login_required
def toggle_visibility(request, character_card_id, characteristic):
    # Отримати характеристику по її ідентифікатору
    try:
        character_card = CharacterCard.objects.get(id=character_card_id)
    except CharacterCard.DoesNotExist:
        return JsonResponse({'error': 'Character card not found'}, status=404)

    # Перевірити, чи користувач є власником цієї характеристики
    if character_card.player != request.user:
        return JsonResponse({'error': 'You are not the owner of this character card'}, status=403)

    # Змінити видимість характеристики згідно з параметром
    if characteristic == 'bio':
        character_card.bio_hidden = not character_card.bio_hidden
    elif characteristic == 'health':
        character_card.health_hidden = not character_card.health_hidden
    elif characteristic == 'phobia':
        character_card.phobia_hidden = not character_card.phobia_hidden
    elif characteristic == 'hobby':
        character_card.hobby_hidden = not character_card.hobby_hidden
    elif characteristic == 'knowledge':
        character_card.knowledge_hidden = not character_card.knowledge_hidden
    elif characteristic == 'additional_info':
        character_card.additional_info_hidden = not character_card.additional_info_hidden
    elif characteristic == 'luggage':
        character_card.luggage_hidden = not character_card.luggage_hidden
    else:
        return JsonResponse({'error': 'Invalid characteristic'}, status=400)

    character_card.save()

    return JsonResponse({'success': 'Visibility toggled successfully'})


def check_end_turn(request):
    room_id = request.GET.get('room_id')
    room = Room.objects.get(id=room_id)

    # Отримуємо всі місця у кімнаті
    places_in_room = Place.objects.filter(room=room)

    # Перевіряємо, чи всі гравці в кімнаті натиснули кнопку "End Turn"
    all_players_finished_turn = all(place.finished_turn for place in places_in_room)

    # Повертаємо відповідь у форматі JSON
    return JsonResponse({'all_players_finished_turn': all_players_finished_turn})


def game_started(request, room_id):
    # Опрацьовуйте початок гри тут
    room = Room.objects.get(id=room_id)
    return render(request, 'game_started.html',
                  {'room': room, 'character_card': CharacterCard.objects.get(player=request.user)})
