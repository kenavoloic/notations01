from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "configurations"

urlpatterns = [
    path('', auth_views.LoginView.as_view(
        template_name = 'configurations/pages/connexion.html'),
         name = 'accueil'),
    path('connexion/', auth_views.LoginView.as_view(
        template_name='configurations/pages/connexion.html'
    ), name='connexion'),
    path('deconnexion/', auth_views.LogoutView.as_view(), name='deconnexion'),
    path('groupes/', views.group_list, name='group_list'),
    path('create/', views.create_group, name='create_group'),
    path('<int:group_id>/', views.group_detail, name='group_detail'),
    path('<int:group_id>/add-user/', views.add_user_to_group, name='add_user_to_group'),
    path('<int:group_id>/remove-user/', views.remove_user_from_group, name='remove_user_from_group'),
    # API endpoints
    path('api/<int:group_id>/add-user/', views.api_add_user, name='api_add_user'),
    path('api/<int:group_id>/remove-user/', views.api_remove_user, name='api_remove_user'),
]
