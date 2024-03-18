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
    return render(request, 'room_detail.html', {'room': room, 'places': places, 'room_id': room_id})


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

    # Отримуємо номер мінімального місця
    min_place_number = places.aggregate(min_place_number=Min('player_number'))['min_place_number']

    # Отримуємо першого гравця для ходу
    first_player = User.objects.filter(place__room=room, place__player_number=min_place_number).first()

    # Якщо немає жодного гравця на мінімальному місці, використовуємо F-об'єкт
    if not first_player:
        first_player = User.objects.filter(place__room=room).annotate(min_place_number=Min('place__player_number')).order_by('min_place_number').first()

    # Позначаємо поточного гравця
    room.current_turn_player = first_player
    room.save()

    # Створюємо характеристики для кожного гравця
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

    # Повертаємо відповідь у форматі JSON, щоб показати, що гра успішно стартувала
    return JsonResponse({'message': 'Game started successfully'})

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

@require_http_methods(["POST"])
def toggle_visibility(request, character_card_id, characteristic):
    # Отримати характеристику по її ідентифікатору
    try:
        character_card = CharacterCard.objects.get(id=character_card_id)
    except CharacterCard.DoesNotExist:
        return JsonResponse({'error': 'Character card not found'}, status=404)

    # Перевірити, чи користувач є власником цієї характеристики
    if character_card.player != request.user:
        return JsonResponse({'error': 'You are not the owner of this character card'}, status=403)

    # Отримати кімнату, з якою пов'язаний character_card
    room = character_card.place.room

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

    players = room.place_set.order_by('player_number').values_list('player_name', flat=True)

    # Визначення поточного гравця, який має робити хід
    current_player_index = players.index(room.current_turn_player.username)
    next_player_index = (current_player_index + 1) % len(players)
    next_player_username = players[next_player_index]

    # Зміна поточного гравця, який має робити хід
    room.current_turn_player = User.objects.get(username=next_player_username)
    room.save()

    return JsonResponse({'success': 'Visibility toggled successfully'})

def game_started(request, room_id):
    # Опрацьовуйте початок гри тут
    room = Room.objects.get(id=room_id)
    return render(request, 'game_started.html', {'room': room, 'character_card': CharacterCard.objects.get(player=request.user)})

