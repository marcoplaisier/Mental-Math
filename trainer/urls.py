from django.urls import path
from . import views

app_name = 'trainer'

urlpatterns = [
    path('', views.index, name='index'),
    path('check/', views.check_answer, name='check_answer'),
    path('statistics/', views.statistics, name='statistics'),
    path('select-user/', views.select_user, name='select_user'),
    path('switch-user/', views.switch_user, name='switch_user'),
]
