from django.contrib import admin
from django.urls import path
from myapp import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('room/<int:room_id>/', views.room_detail, name='room_detail'),
    path('take_place/<int:room_id>/<int:place_id>/', views.take_place, name='take_place'),
    path('delete_room/<int:room_id>/', views.delete_room, name='delete_room'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('start_game/<int:room_id>/', views.start_game, name='start_game'),
    path('game_started/<int:room_id>/', views.game_started, name='game_started'),
    path('character/', views.character_info, name='character_info'),
    path('toggle_visibility/<int:character_card_id>/<str:characteristic>/', views.toggle_visibility, name='toggle_visibility'),
]
