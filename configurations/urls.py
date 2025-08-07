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
]
