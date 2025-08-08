# Imports from Django
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Prefetch
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User

# Imports from local models and forms
from .models import Page, GroupePage, AssociationUtilisateurGroupe, CustomGroup, GroupMembership
from .forms import GroupForm


class GroupAccessMixin:
    required_group = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if self.required_group:
            has_access = AssociationUtilisateurGroupe.objects.filter(
                user = request.user,
                page_group__name = self.required_group
            ).exists()

            if not has_access and not request.user.is_superuser:
                raise PermissionDenied("Vous ne pouvez accéder à cette page.")
        return super().dispatch(request, *args, **kwargs)


    def redirect_to_user_page(self, request):
        user_groups = AssociationUtilisateurGroupe.objects.filter(
            user = request.user
            ).select_related('page_group')

        if user_groups.exists():
            first_group = user_groups.first().page_group
            first_page = Page.objects.filter(
                group = first_group,
                is_active = True
            ).order_by('ordre').first()

            if first_page:
                messages.warning(request, f"Vous n'avez pas accès à cette page. Redirection vers {first_page.nom}")
                return redirect('page_view', page_name=first_page.nom)
        messages.error(request, "Aucune page accessible trouvée.")
        return redirect("accueil")
    


        
class BasePageView(LoginRequiredMixin, GroupAccessMixin, TemplateView):
    """Vue de base pour toutes les pages avec barre navigation dynamique """

    page_name = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user_groups = AssociationUtilisateurGroupe.objects.filter(
            user = self.request.user
            ).select_related('page_group').prefetch_related(
                Prefetch(
                    'page_group__page_set',
                    queryset = Page.objects.filter(is_active=True).order_by('ordre'),
                    to_attr='active_pages'))
        

        navbar_data = {}

        for association in user_groups:
            group = association.page_group
            pages = Page.objects.filter(
                group = group,
                is_active = True
                ).order_by('ordre')

            navbar_data[group] = pages
            context['navbar_groups'] = navbar_data
            context['current_page'] = getattr(self, 'page_name', '')

        return context

def is_group_manager(user):
    """Vérifier si l'utilisateur est membre du groupe 'gestionnaire_groupes'"""
    if not user.is_authenticated:
        return False
    return user.groups.filter(name='gestionnaire_groupes').exists() or user.is_superuser

def group_manager_required(view_func):
    """Décorateur pour vérifier l'appartenance au groupe gestionnaire_groupes"""
    def wrapper(request, *args, **kwargs):
        if not is_group_manager(request.user):
            raise PermissionDenied("Vous devez être membre du groupe 'gestionnaire_groupes' pour accéder à cette page.")
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@group_manager_required
def group_list(request):
    """Afficher la liste des groupes"""
    groups = CustomGroup.objects.all().prefetch_related('members')
    return render(request, 'groups/group_list.html', {'groups': groups})

@login_required
@group_manager_required
def group_detail(request, group_id):
    """Détails d'un groupe avec ses membres"""
    group = get_object_or_404(CustomGroup, id=group_id)
    members = group.members.all()
    all_users = User.objects.exclude(id__in=members.values_list('id', flat=True))
    
    context = {
        'group': group,
        'members': members,
        'all_users': all_users,
        'is_creator': request.user == group.created_by
    }
    return render(request, 'groups/group_detail.html', context)

@login_required
@group_manager_required
def create_group(request):
    """Créer un nouveau groupe"""
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.save()
            # Ajouter le créateur comme membre
            group.add_user(request.user, request.user)
            messages.success(request, f"Groupe {group.name} créé avec succès!")
            return redirect('group_detail', group_id=group.id)
    else:
        form = GroupForm()
    
    return render(request, 'groups/create_group.html', {'form': form})

@login_required
@group_manager_required
@require_http_methods(["POST"])
def add_user_to_group(request, group_id):
    """Ajouter un utilisateur à un groupe"""
    group = get_object_or_404(CustomGroup, id=group_id)
    user_id = request.POST.get('user_id')
    
    if not user_id:
        messages.error(request, "Utilisateur non spécifié.")
        return redirect('group_detail', group_id=group_id)
    
    try:
        user = User.objects.get(id=user_id)
        if group.add_user(user, request.user):
            messages.success(request, f"Utilisateur {user.username} ajouté au groupe.")
        else:
            messages.warning(request, f"Utilisateur {user.username} est déjà membre du groupe.")
    except User.DoesNotExist:
        messages.error(request, "Utilisateur introuvable.")
    
    return redirect('group_detail', group_id=group_id)

@login_required
@group_manager_required
@require_http_methods(["POST"])
def remove_user_from_group(request, group_id):
    """Supprimer un utilisateur d'un groupe"""
    group = get_object_or_404(CustomGroup, id=group_id)
    user_id = request.POST.get('user_id')
    
    if not user_id:
        messages.error(request, "Utilisateur non spécifié.")
        return redirect('group_detail', group_id=group_id)
    
    try:
        user = User.objects.get(id=user_id)
        if group.remove_user(user):
            messages.success(request, f"{user.username} supprimé du groupe.")
        else:
            messages.error(request, f"{user.username} n'est pas membre du groupe.")
    except User.DoesNotExist:
        messages.error(request, 'Utilisateur introuvable.')
    
    return redirect('group_detail', group_id=group_id)

# API pour AJAX
@login_required
@group_manager_required
def api_add_user(request, group_id):
    """API pour ajouter un utilisateur via AJAX"""
    if request.method == 'POST':
        group = get_object_or_404(CustomGroup, id=group_id)
        user_id = request.POST.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
            success = group.add_user(user, request.user)
            return JsonResponse({
                'success': success,
                'message': f'Utilisateur {"ajouté" if success else "déjà membre"}'
            })
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Utilisateur introuvable'})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

@login_required
@group_manager_required
def api_remove_user(request, group_id):
    """API pour supprimer un utilisateur via AJAX"""
    if request.method == 'POST':
        group = get_object_or_404(CustomGroup, id=group_id)
        user_id = request.POST.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
            success = group.remove_user(user)
            return JsonResponse({
                'success': success,
                'message': f'Utilisateur {"supprimé" if success else "non trouvé"}'
            })
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Utilisateur introuvable'})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})
