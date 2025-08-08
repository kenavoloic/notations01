from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.urls import reverse
from django.utils.html import format_html
from django.db import models
from .models import  GroupePage, Page, AssociationUtilisateurGroupe, PageConfig
from .models import CustomGroup, GroupMembership
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
