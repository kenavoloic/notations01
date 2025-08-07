from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.contrib.auth.models import Group, User
from django.urls import reverse

class GroupePage(models.Model):
    """Modèle pour définir les groupes de pages"""
    nom = models.CharField(max_length=50, unique=True)
    libelle = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    ordre = models.IntegerField(default=0, help_text="Ordre d'affichage dans la navbar")
    
    class Meta:
        ordering = ['ordre', 'nom']
    
    def __str__(self):
        return self.libelle

class Page(models.Model):
    """Modèle pour définir les pages et leurs associations aux groupes"""
    nom = models.CharField(max_length=50, unique=True)
    libelle = models.CharField(max_length=255)
    nom_url = models.CharField(max_length=100, help_text="Nom de l'URL Django")
    groupe = models.ForeignKey(GroupePage, on_delete=models.CASCADE, related_name='pages_list')
    ordre = models.IntegerField(default=0, help_text="Ordre dans le groupe")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['groupe', 'ordre', 'nom']
    
    def __str__(self):
        return f"{self.libelle} ({self.groupe.nom})"
    
    def get_url(self):
        """Retourne l'URL de la page"""
        try:
            return reverse(self.nom_url)
        except:
            return "#"

class PageConfig(models.Model):
    """Configuration des pages - PAS le contenu (qui reste dans les templates)"""
    nom = models.CharField(max_length=100, unique=True)  # Identifiant technique
    libelle = models.CharField(max_length=200)       # Nom affiché dans la navbar
    groupe = models.ForeignKey(GroupePage, on_delete=models.CASCADE, related_name='pages_config')
    
    # Routing
    url_pattern = models.CharField(max_length=200)  # 'dashboard/', 'reports/sales/'
    nom_template = models.CharField(max_length=200)  # 'pages/admin/dashboard.html'
    
    # Navigation
    ordre = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)  # Page par défaut du groupe
    show_in_navbar = models.BooleanField(default=True)
    
    titre_page = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['groupe', 'ordre', 'nom']
        unique_together = [['groupe', 'ordre']]
    
    def __str__(self):
        return f"{self.groupe.nom} - {self.libelle}"
    
    def get_titre_complet(self):
        """Titre complet pour le <title>"""
        if self.titre_page:
            return f"{self.titre_page} | Mon App"
        return f"{self.libelle} | Mon App"
    
class AssociationUtilisateurGroupe(models.Model):
    """Association entre utilisateurs et groupes de pages"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    page_group = models.ForeignKey(GroupePage, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ['user', 'page_group']
    
    def __str__(self):
        return f"{self.user.username} - {self.page_group.nom}"


