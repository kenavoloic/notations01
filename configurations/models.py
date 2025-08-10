from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.contrib.auth.models import Group, User
from django.urls import reverse
from django.core.exceptions import ValidationError
from datetime import date
from django.db.models import Q

# Gestion des groupes
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


class CustomGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(User, through='GroupMembership', related_name='custom_groups', through_fields=('group', 'user'))
    
    def __str__(self):
        return self.name
    
    def add_user(self, user, added_by=None):
        """Ajouter un utilisateur au groupe"""
        membership, created = GroupMembership.objects.get_or_create(
            group=self,
            user=user,
            defaults={'added_by': added_by}
        )
        return created
    
    def remove_user(self, user):
        """Supprimer un utilisateur du groupe"""
        try:
            membership = GroupMembership.objects.get(group=self, user=user)
            membership.delete()
            return True
        except GroupMembership.DoesNotExist:
            return False
    
    def is_member(self, user):
        """Vérifier si un utilisateur est membre du groupe"""
        return self.members.filter(id=user.id).exists()
    
    def get_members_count(self):
        """Obtenir le nombre de membres"""
        return self.members.count()

class GroupMembership(models.Model):
    group = models.ForeignKey(CustomGroup, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='added_memberships')
    
    class Meta:
        unique_together = ('group', 'user')
    
    def __str__(self):
        return f"{self.user.username} in {self.group.name}"
#=========================================================
# ==================== Logique métier ====================
# Questionnement : on_delete=models.CASCADE ou on_delete=models.PROTECT ?
# Pour l'instant CASCADE mais très certainement PROTECT 

# ==================== MANAGERS PERSONNALISÉS ====================

# class ConducteurActiveManager(models.Manager):
#     """Manager pour récupérer uniquement les conducteurs actifs"""
#     def get_queryset(self):
#         hoy = date.today()
#         return super().get_queryset().filter(
#             actif_p=True,
#             (models.Q(date_sortie__isnull=True) | models.Q(date_sortie__gt=hoy))
#         )


# class ConducteurActiveManager(models.Manager):
#     """Manager pour récupérer uniquement les conducteurs actifs"""
#     def get_queryset(self):
#         hoy = date.today()
#         return super().get_queryset().filter(
#             actif_p=True,
#             Q(date_sortie__isnull=True) | Q(date_sortie__gt=hoy)
#         )

class ConducteurActiveManager(models.Manager):
    """Manager pour récupérer uniquement les conducteurs actifs"""
    def get_queryset(self):
        aujourd_hui = date.today()
        # Conducteurs sans date de sortie OU avec date de sortie future
        condition_date = Q(date_sortie__isnull=True) | Q(date_sortie__gt=aujourd_hui)
        
        return super().get_queryset().filter(
            actif_p=True
        ).filter(condition_date)

class NotationRecentManager(models.Manager):
    """Manager pour les notations récentes (6 derniers mois)"""
    def get_queryset(self):
        from datetime import datetime, timedelta
        six_months_ago = date.today() - timedelta(days=180)
        return super().get_queryset().filter(date_notation__gte=six_months_ago)


#=========================================================
class Societe(models.Model):
    nom = models.CharField(max_length=255, help_text="Nom de la société")
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    
    def __str__(self):
        return self.nom

    def clean(self):
        if self.nom:
            self.nom = self.nom.strip()
        if not self.nom:
            raise ValidationError({'nom':"Un nom de société est requis."})

    class Meta:
        verbose_name = "Société"
        verbose_name_plural = "Sociétés"
        ordering = ['nom']
        indexes = [models.Index(fields=['nom']),]

class Service(models.Model):
    nom = models.CharField(max_length=255, help_text="Nom du service")
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    
    def __str__(self):
        return self.nom

    def clean(self):
        if self.nom:
            self.nom = self.nom.strip()
        if not self.nom:
            raise ValidationError({'nom': "Un nom de service est requis."})

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['nom']
        indexes = [models.Index(fields=['nom']),]
    
class Site(models.Model):
    nom = models.CharField(max_length=255, help_text="Commune du site")
    code_postal = models.CharField(
        max_length=5,
        #validators=[RegexValidator(regex=r'^\d{5}$', message='Un code postal français contient 5 caractères')],
        validators=[RegexValidator(r'^\d{5}$', message='Un code postal français contient 5 caractères')],
        help_text="Code postal français sur 5 caractères."
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.nom} ({self.code_postal})"

    def clean(self):
        if self.nom:
            self.nom = self.nom.strip()
        if not self.nom:
            raise ValidationError({'nom':"Un nom de commune est requis."})

    class Meta:
        verbose_name = "Site"
        verbose_name_plural = "Sites"
        ordering = ['code_postal','nom']
        unique_together = ['code_postal','nom']
        indexes = [
            models.Index(fields=['code_postal']),
            models.Index(fields=['nom']),
        ]

class Conducteur(models.Model):
    erp_id = models.IntegerField(unique=True, help_text="Identifiant du conducteur dans l'ERP.")
    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255)
    nom_slug = models.CharField(max_length=255, blank=True, help_text="Nom original pour l'affichage")
    prenom_slug = models.CharField(max_length=255, blank=True, help_text="Prénom original pour l'affichage")    
    date_naissance = models.DateField(null=True, blank=True, help_text="Date de naissance (optionnelle).")
    date_entree = models.DateField(help_text="Date d'embauche")
    date_sortie = models.DateField(null=True, blank=True, help_text="Date de fin de contrat.")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, help_text="Nom du service d'affectation.")
    site = models.ForeignKey(Site, on_delete=models.CASCADE, help_text="Nom du site d'affectation.")
    societe = models.ForeignKey(Societe, on_delete=models.CASCADE, help_text="Nom de la société d'affectation.")
    actif_p = models.BooleanField(default=True, verbose_name="Actif", help_text="Conducteur actif ?")
    interim_p = models.BooleanField(default=False, verbose_name="Intérim", help_text="Conducteur intérimaire ?")

    objects = models.Manager()
    actifs = ConducteurActiveManager()

    def __str__(self):
        return f"{self.prenom_affichage} {self.nom_affichage}"

    @property
    def nom_complet(self):
        return f"{self.prenom_affichage} {self.nom_affichage}"


    def save(self, *args, **kwargs):
        # Si c'est une création (pas d'ID) ou si les champs slug sont vides
        is_new = self.pk is None
        
        if self.nom:
            if is_new or not self.nom_slug:
                self.nom_slug = self.nom
            self.nom = self.nom.lower()
            
        if self.prenom:
            if is_new or not self.prenom_slug:
                self.prenom_slug = self.prenom
            self.prenom = self.prenom.lower()
        
        super().save(*args, **kwargs)
    
    @property
    def nom_affichage(self):
        return self.nom_slug if self.nom_slug else self.nom
    
    @property
    def prenom_affichage(self):
        return self.prenom_slug if self.prenom_slug else self.prenom

    @property
    def est_actuellement_actif(self):
        if self.actif_p:
            return True
        return False

    @property
    def age(self):
        if not self.date_naissance:
            return None
        hoy = date.today()
        return hoy.year - self.date_naissance.year - ((hoy.month, hoy.day) < (self.date_naissance.month, self.date_naissance.day))

    @property
    def anciennete_jours(self):
        fin = self.date_sortie if self.date_sortie else date.today()
        return (fin - self.date_entree).days 

    def clean(self):
        """Validation métier"""
        erreurs = {}

        # Validation des noms
        if self.nom:
            self.nom = self.nom.strip().title()
        if self.prenom:
            self.prenom = self.prenom.strip().title()
        
        if not self.nom:
            erreurs['nom'] = 'Le nom ne peut pas être vide.'
        if not self.prenom:
            erreurs['prenom'] = 'Le prénom ne peut pas être vide.'

        # Validation des dates
        if self.date_naissance and self.date_naissance >= self.date_entree:
            erreurs['date_naissance'] = "La date de naissance doit être antérieure à la date d'entrée."
        
        if self.date_naissance and self.date_naissance > date.today():
            erreurs['date_naissance'] = 'La date de naissance ne peut pas être dans le futur.'
        
        if self.date_entree > date.today():
            erreurs['date_entree'] = "La date d'entrée ne peut pas être dans le futur."
        
        if self.date_sortie:
            if self.date_sortie <= self.date_entree:
                erreurs['date_sortie'] = "La date de sortie doit être postérieure à la date d'entrée."
            if self.date_sortie > date.today():
                erreurs['date_sortie'] = "La date de sortie ne peut pas être dans le futur."

        # Validation de cohérence
        if not self.actif_p and not self.date_sortie:
            erreurs['date_sortie'] = 'Un conducteur inactif doit avoir une date de sortie.'
        
        if self.date_sortie and self.actif_p:
            erreurs['actif_p'] = 'Un conducteur avec une date de sortie passée ne peut pas être actif.'

        if erreurs:
            raise ValidationError(erreurs)
        
    class Meta:
        verbose_name = "Conducteur"
        verbose_name_plural = "Conducteurs"
        ordering = ['nom', 'prenom']
        indexes = [
            models.Index(fields=['nom', 'prenom']),
            models.Index(fields=['erp_id']),
            models.Index(fields=['actif_p', 'date_sortie']),
            models.Index(fields=['service', 'site']),
        ]

class Notateur(models.Model):
    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255)
    nom_slug = models.CharField(max_length=255, blank=True, help_text="Nom original pour l'affichage")
    prenom_slug = models.CharField(max_length=255, blank=True, help_text="Prénom original pour l'affichage")
    date_entree = models.DateField(null=True, blank=True, help_text="Date d'embauche")
    date_sortie = models.DateField(null=True, blank=True, help_text="Date de fin de contrat")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, help_text="Service d'affectation")

    def save(self, *args, **kwargs):
        # Si c'est une création (pas d'ID) ou si les champs slug sont vides
        is_new = self.pk is None
        
        if self.nom:
            if is_new or not self.nom_slug:
                self.nom_slug = self.nom
            self.nom = self.nom.lower()
            
        if self.prenom:
            if is_new or not self.prenom_slug:
                self.prenom_slug = self.prenom
            self.prenom = self.prenom.lower()
        
        super().save(*args, **kwargs)

    @property
    def nom_affichage(self):
        return self.nom_slug if self.nom_slug else self.nom
    
    @property
    def prenom_affichage(self):
        return self.prenom_slug if self.prenom_slug else self.prenom

        
    def __str__(self):
        return f"{self.prenom_affichage} {self.nom_affichage}"

    @property
    def nom_complet(self):
        return f"{self.prenom_affichage} {self.nom_affichage}"

    @property
    def est_actif(self):
        """Vérifie si le notateur est actuellement actif"""
        return not self.date_sortie or self.date_sortie > date.today()

    def clean(self):
        """Validation métier"""
        erreurs = {}

        # Validation des noms
        if self.nom:
            self.nom = self.nom.strip().title()
        if self.prenom:
            self.prenom = self.prenom.strip().title()
        
        if not self.nom:
            erreurs['nom'] = 'Le nom ne peut pas être vide.'
        if not self.prenom:
            erreurs['prenom'] = 'Le prénom ne peut pas être vide.'

        # Validation des dates
        if self.date_entree > date.today():
            erreurs['date_entree'] = "La date d'entrée ne peut pas être dans le futur."
        
        if self.date_sortie:
            if self.date_sortie <= self.date_entree:
                erreurs['date_sortie'] = "La date de sortie doit être postérieure à la date d'entrée."
            if self.date_sortie > date.today():
                erreurs['date_sortie'] = 'La date de sortie ne peut pas être dans le futur.'

        if erreurs:
            raise ValidationError(erreurs)
        
    class Meta:
        verbose_name = "Notateur"
        verbose_name_plural = "Notateurs"
        ordering = ['nom', 'prenom']
        indexes = [
            models.Index(fields=['nom', 'prenom']),
            models.Index(fields=['date_sortie']),
        ]
        
class CriteresNotation(models.Model):
    nom = models.CharField(max_length=255, help_text="Nom du critère de notation")
    description = models.TextField(blank=True, help_text="Description")
    valeur_mini = models.IntegerField(help_text="Valeur plancher")
    valeur_maxi = models.IntegerField(help_text="Valeur plafond")
    actif = models.BooleanField(default=True, help_text="Critère actuellement utilisé")    
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.nom} {self.valeur_mini}-{self.valeur_maxi}"

    @property
    def plage_valeurs(self):
        return f"{self.valeur_mini} à {self.valeur_maxi}"

    def clean(self):
        """Validation métier"""
        erreurs = {}

        if self.nom:
            self.nom = self.nom.strip()
        if not self.nom:
            erreurs['nom'] = 'Le nom du critère ne peut pas être vide.'

        if self.valeur_mini >= self.valeur_maxi:
            erreurs['valeur_maxi'] = 'La valeur maximale doit être supérieure à la valeur minimale.'
        
        if self.valeur_mini < 0:
            erreurs['valeur_mini'] = 'La valeur minimale ne peut pas être négative.'

        if erreurs:
            raise ValidationError(erreurs)

        
    class Meta:
        verbose_name = "Critère de notation"
        verbose_name_plural = "Critères de notation"
        ordering = ['nom']
        indexes = [
            models.Index(fields=['nom']),
            models.Index(fields=['actif']),
        ]

class Notation(models.Model):
    date_notation = models.DateField(help_text="Date de la notation")
    notateur = models.ForeignKey(Notateur, on_delete=models.CASCADE, help_text="")
    conducteur = models.ForeignKey(Conducteur, on_delete=models.CASCADE, help_text="")
    critere = models.ForeignKey(CriteresNotation, on_delete=models.CASCADE, help_text="")
    valeur = models.IntegerField(null=True, blank=True, help_text="")

    def __str__(self):
        return f"{self.conducteur} - {self.critere} : {self.valeur}"

    class Meta:
        verbose_name = "Notation"
        verbose_name_plural = "Notations"
        unique_together = ['conducteur', 'critere', 'date_notation', 'notateur']

class HistoriqueNotation(models.Model):
    notation = models.ForeignKey(Notation, on_delete=models.CASCADE)
    notateur = models.ForeignKey(Notateur, on_delete=models.CASCADE)
    conducteur = models.ForeignKey(Conducteur, on_delete=models.CASCADE)
    critere = models.ForeignKey(CriteresNotation, on_delete=models.CASCADE)
    ancienne_valeur = models.IntegerField(null=True, blank=True)
    nouvelle_valeur = models.IntegerField()
    date_changement = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Historique de notation"
        verbose_name_plural = "Historiques de notation"

class HistoriqueSite(models.Model):
    conducteur = models.ForeignKey(Conducteur, on_delete=models.CASCADE)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    date_entree = models.DateField()
    date_sortie = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Historique de site"
        verbose_name_plural = "Historiques de site"



        
