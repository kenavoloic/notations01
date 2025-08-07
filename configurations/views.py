from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib import messages

from django.contrib.auth.views import LoginView

from django.core.exceptions import PermissionDenied
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch
from . models import Page, GroupePage, AssociationUtilisateurGroupe

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
