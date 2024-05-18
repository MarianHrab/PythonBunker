from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate
from django.shortcuts import redirect
from .forms import RoomForm
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from .models import Place, CharacterCard
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Room, Vote
import random
from django.db import transaction
from collections import Counter
from django.db.models import Count
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib import messages

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
    # Якщо форму було надіслано
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.creator = request.user  # Зберігаємо користувача, який створив кімнату
            room.players_count = request.POST.get('players_count')  # Отримати значення players_count
            room.save()
            return redirect('index')  # Перенаправлення на головну сторінку
    else:
        form = RoomForm()

    # Отримати всі кімнати
    rooms = Room.objects.all()

    # Передача кімнат та форми в контекст шаблону
    context = {
        'rooms': rooms,
        'form': form,
    }

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
    messages.success(request, 'Game started!')
    # Повертаємо відповідь JSON, що підтверджує успішний початок гри
    return redirect('room_detail', room_id=room_id)


def endTurn(request, room_id):
    # Отримати об'єкт кімнати за room_id
    room = get_object_or_404(Room, id=room_id)
    voting_id_room = room_id

    # Перевірка, чи гра взагалі розпочалася
    if not room.game_started:
        return JsonResponse({'error': 'Гра ще не розпочалася'}, status=400)

    # Отримати місце поточного гравця
    place = Place.objects.filter(room=room, player_name=request.user.username).first()

    # Перевірити, чи гравець перебуває в цій кімнаті
    if not place:
        return JsonResponse({'error': 'Ви не перебуваєте в цій кімнаті'}, status=400)

    # Перевірити, чи хід гравця вже завершено
    if place.turn_finished:
        return JsonResponse({'error': 'Ви вже завершили свій хід'}, status=400)

    # Перевірити, чи гравець може закінчити хід
    if not place.can_end_turn:
        return JsonResponse({'error': 'Ви не можете завершити свій хід'}, status=400)

    place.turn_finished = True
    place.can_end_turn = False
    place.save()

    # Отримати ідентифікатор поточного місця
    current_place_id = place.id

    # Отримати наступного гравця
    next_place = Place.objects.filter(room=room, id__gt=current_place_id, is_kicked=False).first()
    all_players_finished_turn = all(place.turn_finished for place in room.place_set.all())

    # Перевірка, чи є наступний гравець
    if next_place is None:
        # Якщо немає наступного гравця, візьмемо першого гравця
        if all_players_finished_turn:
            # Якщо всі гравці завершили хід, почати голосування за вигнання гравця
            start_voting(voting_id_room)
        return JsonResponse({'message': 'Всі гравці завершили хід'})
    else:
        next_player_name = next_place.player_name
        # Отримати об'єкт користувача за його ім'ям
        next_player = User.objects.get(username=next_player_name)

        # Оновити поле current_turn_player на наступного гравця
        room.current_turn_player = next_player
        room.save()

        # Повернути підтвердження у форматі JSON
        return JsonResponse({'message': 'Хід завершено успішно'})


def start_voting(room_id):
    room = get_object_or_404(Room, id=room_id)

    # Перевірка, чи гра взагалі розпочалася
    if not room.game_started:
        return JsonResponse({'error': 'Гра ще не розпочалася'}, status=400)

    # Отримати всі місця у кімнаті
    places_in_room = Place.objects.filter(room=room)

    # Перевірка, чи всі гравці завершили хід
    all_players_finished_turn = all(place.turn_finished for place in places_in_room)

    if not all_players_finished_turn:
        return JsonResponse({'error': 'Не всі гравці завершили свій хід'}, status=400)

    # Позначаємо початок голосування
    room.voting_started = True
    room.turn_ended = True
    room.save()

    return JsonResponse({'message': 'Голосування розпочато'})


def vote_endpoint(request, room_id):
    if request.method == 'POST':
        selected_player_name = request.POST.get('selected_player_name')

        # Перевірка, чи вибраний гравець переданий у запиті
        if not selected_player_name:
            return JsonResponse({'error': 'No player for voting'}, status=400)

        # Отримання поточного користувача, який голосує
        voter = request.user

        # Отримання кімнати, у якій відбувається голосування
        room_id = request.POST.get('room_id')
        room = get_object_or_404(Room, id=room_id)

        # Перевірка, чи гравець знаходиться у кімнаті і грає в гру
        try:
            place = Place.objects.get(room=room, player_name=voter.username)
        except Place.DoesNotExist:
            return JsonResponse({'error': 'You are not able to vote'}, status=400)

        # Отримання об'єкта гравця, на якого голосують
        try:
            target_player = User.objects.get(username=selected_player_name)
        except User.DoesNotExist:
            return JsonResponse({'error': 'No player found'}, status=400)

        # Створення нового голосу
        Vote.objects.create(voter=voter, target_player=target_player, room=room)

        # Оновлення поля voted для гравця
        place.voted = True
        place.save()

        # Перевірка, чи всі гравці вже проголосували
        all_players_voted = all(place.voted for place in room.place_set.all())

        if all_players_voted:
            # Завершення голосування
            winners = determine_winner(room_id)
            # Отримання імен користувачів переможців
            winner_names = ', '.join(winner.username for winner in winners)
            for winner in winners:
                winner_place = Place.objects.get(room=room, player_name=winner.username)
                winner_place.is_kicked = True
                winner_place.save()
            # Створення повідомлення для pop-up
            message = f'Player {winner_names} as a voting result'
            messages.success(request, 'Player {winner_names} as a voting result!')
            # Початок нового ходу після завершення голосування
            start_new_turn(room_id)
            # Відправлення JSON відповіді з повідомленням
            return JsonResponse({'message': message}, status=200)
        else:
            # Повернення повідомлення про успішне голосування
            return JsonResponse({'message': 'Voted counted'}, status=200)
    else:
        return JsonResponse({'error': 'No method'}, status=405)


def end_game(room):
    room.game_finished = True
    room.save()
    return JsonResponse({'error': 'Game finished'}, status=200)


def start_new_turn(room_id):
    room = get_object_or_404(Room, id=room_id)
    # Отримуємо всіх гравців кімнати
    players = room.place_set.all()
    # Отримуємо загальну кількість гравців на початку гри
    # initial_players_count = room.initial_players_count
    initial_players_count = room.place_set.count()
    # Підраховуємо кількість живих гравців
    alive_players_count = players.filter(is_kicked=False).count()

    # Перевіряємо, чи досягнута умова для завершення гри
    if alive_players_count == initial_players_count // 2 or alive_players_count == (initial_players_count // 2) + 1:
        # Якщо так, гра закінчується
        end_game(room)
    else:
        # Отримати всі місця у кімнаті
        places_in_room = Place.objects.filter(room=room)

        # Вибрати першого гравця в кімнаті для початку нового ходу
        first_place = places_in_room.filter(is_kicked=False).first()  # Фільтруємо за is_kicked
        if first_place:
            first_player = User.objects.get(username=first_place.player_name)
            room.current_turn_player = first_player
            room.save()

            # Почати новий хід для кожного місця у кімнаті, якщо гравець не вигнаний
            for place in places_in_room:
                if not place.is_kicked:
                    place.turn_finished = False
                    place.can_end_turn = True
                    place.voted = False
                    place.save()

        # Оновити статус гри
        room.game_started = True
        room.voting_started = False
        room.turn_ended = False
        room.save()

        return JsonResponse({'message': 'New turn'})


def calculate_votes(room_id):
    room = Room.objects.get(id=room_id)
    all_votes = Vote.objects.filter(room=room)
    vote_counter = Counter(vote.target_player for vote in all_votes)
    return vote_counter


def determine_winner(room_id):
    vote_counter = calculate_votes(room_id)
    if vote_counter:
        max_votes = max(vote_counter.values())
        winners = [player for player, votes in vote_counter.items() if votes == max_votes]
        return winners
    else:
        return None


def get_vote_results(request, room_id):
    # Отримати кількість голосів за кожного гравця у вказаній кімнаті
    vote_counts = (
        Vote.objects.filter(room_id=room_id)
        .values('target_player__username')  # Групувати за іменем гравця, за якого проголосували
        .annotate(total_votes=Count('id'))  # Підрахунок кількості голосів за кожного гравця
    )

    # Перетворюємо QuerySet в список словників
    vote_counts_list = list(vote_counts)

    # Повертаємо результат у форматі JSON
    return JsonResponse({'voteCounts': vote_counts_list}, encoder=DjangoJSONEncoder)


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

    character_card.characteristic_opened = True
    character_card.save()

    return JsonResponse({'success': 'Visibility toggled successfully'})


def rules(request):
    return render(request, 'rules.html')


def contacts(request):
    return render(request, 'contacts.html')
