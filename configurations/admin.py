from datetime import date
from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.urls import reverse
from django.utils.html import format_html
from django.db import models
from .models import  GroupePage, Page, AssociationUtilisateurGroupe, PageConfig
from .models import CustomGroup, GroupMembership
from . models import  Societe, Service, Site, Conducteur, Notateur, CriteresNotation, Notation, HistoriqueNotation, HistoriqueSite
# Relations pages et groupes
admin.site.register(GroupePage)
admin.site.register(Page)
admin.site.register(PageConfig)
admin.site.register(AssociationUtilisateurGroupe)
#admin.site.register(CustomGroup)
# Extension de l'admin des utilisateurs pour afficher les permissions
class CustomUserAdmin(UserAdmin):
    """Administration utilisateur personnalisée"""
    
    def get_list_display(self, request):
        # Ajouter une colonne pour voir qui est gestionnaire de groupes
        list_display = list(super().get_list_display(request))
        list_display.append('is_group_manager')
        return list_display
    
    def is_group_manager(self, obj):
        """Afficher si l'utilisateur est gestionnaire de groupes"""
        is_manager = obj.groups.filter(name='gestionnaire_groupes').exists()
        if is_manager:
            return format_html('<span style="color: green;">✅ Gestionnaire</span>')
        else:
            return format_html('<span style="color: red;">❌ Non gestionnaire</span>')
    
    is_group_manager.short_description = 'Gestionnaire de groupes'
    is_group_manager.admin_order_field = 'groups'

# Administration pour les groupes personnalisés
class CustomGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at', 'get_members_count', 'view_members_link']
    list_filter = ['created_at', 'created_by']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'view_members_list']
    fields = ['name', 'description', 'created_by', 'created_at', 'view_members_list']
    
    def get_members_count(self, obj):
        count = obj.get_members_count()
        return format_html('<strong>{}</strong> membres', count)
    get_members_count.short_description = 'Nombre de membres'
    
    def view_members_link(self, obj):
        """Lien vers la page de détail du groupe"""
        if obj.pk:
            url = reverse('admin:configurations_groupmembership_changelist')
            return format_html(
                '<a href="{}?group__id__exact={}" target="_blank">Voir les membres</a>',
                url, obj.pk
            )
        return '-'
    view_members_link.short_description = 'Actions'
    
    def view_members_list(self, obj):
        """Afficher la liste des membres dans l'admin"""
        if obj.pk:
            members = obj.members.all()
            if members:
                member_list = []
                for member in members:
                    try:
                        membership = GroupMembership.objects.get(group=obj, user=member)
                        member_info = f"{member.username}"
                        if member.first_name or member.last_name:
                            member_info += f" ({member.first_name} {member.last_name})"
                        member_info += f" - Ajouté le {membership.added_at.strftime('%d/%m/%Y')}"
                        if membership.added_by:
                            member_info += f" par {membership.added_by.username}"
                        member_list.append(member_info)
                    except GroupMembership.DoesNotExist:
                        member_list.append(f"{member.username} (données incomplètes)")
                
                return format_html('<br>'.join(member_list))
            else:
                return "Aucun membre"
        return "Groupe non sauvegardé"
    
    view_members_list.short_description = 'Membres actuels'

class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ['group', 'user', 'added_at', 'added_by']
    list_filter = ['added_at', 'group', 'added_by']
    search_fields = ['group__name', 'user__username', 'user__first_name', 'user__last_name']
    autocomplete_fields = ['user', 'added_by']
    readonly_fields = ['added_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('group', 'user', 'added_by')

# Configuration spéciale pour le groupe gestionnaire_groupes
class GroupManagerGroupAdmin(GroupAdmin):
    """Administration spécialisée pour le groupe gestionnaire_groupes"""
    
    def get_queryset(self, request):
        # Ne montrer que le groupe gestionnaire_groupes
        qs = super().get_queryset(request)
        return qs.filter(name='gestionnaire_groupes')
    
    def has_add_permission(self, request):
        # Empêcher la création de nouveaux groupes depuis cette vue
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Empêcher la suppression du groupe gestionnaire_groupes
        if obj and obj.name == 'gestionnaire_groupes':
            return False
        return super().has_delete_permission(request, obj)
    
    def changelist_view(self, request, extra_context=None):
        # Créer le groupe s'il n'existe pas
        group, created = Group.objects.get_or_create(name='gestionnaire_groupes')
        if created:
            self.message_user(request, 'Groupe "gestionnaire_groupes" créé automatiquement.')
        
        extra_context = extra_context or {}
        extra_context['title'] = 'Gestion du groupe "gestionnaire_groupes"'
        extra_context['subtitle'] = 'Ajoutez ou retirez des utilisateurs pour gérer les permissions de gestion des groupes'
        
        return super().changelist_view(request, extra_context)

# Créer une instance proxy pour avoir une section séparée dans l'admin
class GroupManagerGroup(Group):
    class Meta:
        proxy = True
        verbose_name = "Gestionnaire de groupes"
        verbose_name_plural = "🔑 Gestionnaires de groupes"

# Désenregistrer et réenregistrer seulement si nécessaire
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, CustomUserAdmin)

# Enregistrer nos modèles
admin.site.register(CustomGroup, CustomGroupAdmin)
admin.site.register(GroupMembership, GroupMembershipAdmin)
admin.site.register(GroupManagerGroup, GroupManagerGroupAdmin)

# Personnalisation de l'interface admin
admin.site.site_header = "Administration - Gestion des Groupes"
admin.site.site_title = "Admin Groupes"
admin.site.index_title = "Panneau d'administration"

#Signal pour créer automatiquement le groupe au démarrage
from django.db.models.signals import post_migrate
from django.dispatch import receiver

@receiver(post_migrate)
def create_group_manager_group(sender, **kwargs):
    """Créer automatiquement le groupe gestionnaire_groupes après les migrations"""
    if sender.name == 'configurations':  # Remplacez par le nom de votre app
        Group.objects.get_or_create(name='gestionnaire_groupes')

# ==================== LOGIQUE MÉTIER ====================

@admin.register(Societe)
class SocieteAdmin(admin.ModelAdmin):
    list_display = ('nom', 'nb_conducteurs', 'created_at')
    search_fields = ('nom',)
    readonly_fields = ('created_at',)
    
    def nb_conducteurs(self, obj):
        return obj.conducteur_set.count()
    nb_conducteurs.short_description = 'Nb conducteurs'

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('nom', 'nb_conducteurs', 'nb_notateurs', 'created_at')
    search_fields = ('nom',)
    readonly_fields = ('created_at',)
    
    def nb_conducteurs(self, obj):
        return obj.conducteur_set.count()
    nb_conducteurs.short_description = 'Nb conducteurs'
    
    def nb_notateurs(self, obj):
        return obj.notateur_set.count()
    nb_notateurs.short_description = 'Nb notateurs'

@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code_postal', 'nb_conducteurs', 'created_at')
    list_filter = ('code_postal',)
    search_fields = ('nom', 'code_postal')
    readonly_fields = ('created_at',)
    
    def nb_conducteurs(self, obj):
        return obj.conducteur_set.count()
    nb_conducteurs.short_description = 'Nb conducteurs'


@admin.register(Conducteur)
class ConducteurAdmin(admin.ModelAdmin):
    list_display = ('erp_id', 'nom', 'prenom', 'service', 'site', 'societe', 'actif_p', 'interim_p', 'age_display', 'anciennete_display')
    list_filter = ('actif_p', 'interim_p', 'service', 'site', 'societe', 'date_entree')
    search_fields = ('nom', 'prenom', 'erp_id')
    readonly_fields = ('erp_id', 'age_display', 'anciennete_display', 'nom_complet')
    list_editable = ('actif_p', 'interim_p')
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('erp_id', 'nom', 'prenom', 'date_naissance', 'age_display')
        }),
        ('Affectation', {
            'fields': ('service', 'site', 'societe')
        }),
        ('Dates de service', {
            'fields': ('date_entree', 'date_sortie', 'anciennete_display')
        }),
        ('Statut', {
            'fields': ('actif_p', 'interim_p')
        }),
    )
    
    def statut_actif(self, obj):
        if obj.actif_p and (not obj.date_sortie or obj.date_sortie > date.today()):
            return format_html('<span style="color: green;">✓ Actif</span>')
        return format_html('<span style="color: red;">✗ Inactif</span>')
    statut_actif.short_description = 'Statut'
    
    def age_display(self, obj):
        age = obj.age
        return f"{age} ans" if age else "Non renseigné"
    age_display.short_description = 'Âge'
    
    def anciennete_display(self, obj):
        jours = obj.anciennete_jours if obj.anciennete_jours > 0 else 0
        if jours < 365:
            return f"{jours} jours"
        annees = jours // 365
        return f"{annees} an{'s' if annees > 1 else ''}"
    anciennete_display.short_description = 'Ancienneté'
    
    # Actions personnalisées
    actions = ['marquer_actif', 'marquer_inactif']
    
    def marquer_actif(self, request, queryset):
        updated = queryset.update(actif_p=True)
        self.message_user(request, f"{updated} conducteur{'s' if updated > 1 else ''} marqué{'s' if updated > 1 else ''} comme actif{'s' if updated > 1 else ''}.")
    marquer_actif.short_description = "Marquer comme actif"
    
    def marquer_inactif(self, request, queryset):
        updated = queryset.update(actif_p=False)
        self.message_user(request, f"{updated} conducteur{'s' if updated > 1 else ''} marqué{'s' if updated > 1 else ''} comme inactif{'s' if updated > 1 else ''}.")
    marquer_inactif.short_description = "Marquer comme inactif"
    
@admin.register(Notateur)
class NotateurAdmin(admin.ModelAdmin):
    list_display = ('nom_complet', 'service', 'statut_actif', 'nb_notations')
    list_filter = ('service', 'date_entree', 'date_sortie')
    search_fields = ('nom', 'prenom')
    readonly_fields = ('nom_complet',)
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('nom', 'prenom', 'nom_complet')
        }),
        ('Affectation', {
            'fields': ('service',)
        }),
        ('Dates de service', {
            'fields': ('date_entree', 'date_sortie')
        }),
    )
    
    def statut_actif(self, obj):
        if obj.est_actif:
            return format_html('<span style="color: green;">✓ Actif</span>')
        return format_html('<span style="color: red;">✗ Inactif</span>')
    statut_actif.short_description = 'Statut'
    
    def nb_notations(self, obj):
        return obj.notation_set.count()
    nb_notations.short_description = 'Nb notations'

@admin.register(CriteresNotation)
class CriteresNotationAdmin(admin.ModelAdmin):
    list_display = ('nom', 'plage_valeurs', 'actif', 'nb_notations', 'created_at')
    list_filter = ('actif', 'created_at')
    search_fields = ('nom', 'description')
    list_editable = ('actif',)
    readonly_fields = ('created_at', 'plage_valeurs')
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'description', 'actif')
        }),
        ('Valeurs', {
            'fields': ('valeur_mini', 'valeur_maxi', 'plage_valeurs')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def nb_notations(self, obj):
        return obj.notation_set.count()
    nb_notations.short_description = 'Nb notations'

@admin.register(Notation)
class NotationAdmin(admin.ModelAdmin):
    list_display = ('conducteur', 'critere', 'valeur', 'notateur', 'date_notation')
    list_filter = ('critere', 'notateur', 'date_notation', 'conducteur__service')
    search_fields = ('conducteur__nom', 'conducteur__prenom', 'critere__nom')
    date_hierarchy = 'date_notation'
    autocomplete_fields = ('conducteur', 'notateur', 'critere')
    
    fieldsets = (
        ('Notation', {
            'fields': ('date_notation', 'conducteur', 'critere', 'valeur')
        }),
        ('Notateur', {
            'fields': ('notateur',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'conducteur', 'notateur', 'critere'
        )

@admin.register(HistoriqueNotation)
class HistoriqueNotationAdmin(admin.ModelAdmin):
    list_display = ('notation', 'conducteur', 'critere', 'ancienne_valeur', 'nouvelle_valeur', 'date_changement')
    list_filter = ('critere', 'date_changement')
    search_fields = ('conducteur__nom', 'conducteur__prenom')
    readonly_fields = ('notation', 'notateur', 'conducteur', 'critere', 'ancienne_valeur', 'nouvelle_valeur', 'date_changement')
    date_hierarchy = 'date_changement'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(HistoriqueSite)
class HistoriqueSiteAdmin(admin.ModelAdmin):
    list_display = ('conducteur', 'site', 'date_entree', 'date_sortie', 'duree_affectation')
    list_filter = ('site', 'date_entree', 'date_sortie')
    search_fields = ('conducteur__nom', 'conducteur__prenom', 'site__nom')
    date_hierarchy = 'date_entree'
    autocomplete_fields = ('conducteur', 'site')
    
    def duree_affectation(self, obj):
        fin = obj.date_sortie or date.today()
        duree = (fin - obj.date_entree).days
        if duree < 30:
            return f"{duree} jours"
        elif duree < 365:
            mois = duree // 30
            return f"{mois} mois"
        else:
            annees = duree // 365
            return f"{annees} an{'s' if annees > 1 else ''}"
    duree_affectation.short_description = 'Durée'

# Personnalisation du site d'administration
admin.site.site_header = "Administration - Gestion des Conducteurs"
admin.site.site_title = "Admin Conducteurs"
admin.site.index_title = "Tableau de bord"
