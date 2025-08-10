# configurations/management/commands/dump_conducteurs_actifs.py
from django.core.management.base import BaseCommand
from django.core import serializers
from configurations.models import Conducteur
import json
from datetime import date

class Command(BaseCommand):
    help = 'Dump des conducteurs actifs uniquement avec options avancées'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='conducteurs_actifs.json',
            help='Fichier de sortie (défaut: conducteurs_actifs.json)'
        )
        parser.add_argument(
            '--format',
            type=str,
            default='json',
            choices=['json', 'xml', 'yaml'],
            help='Format de sortie (défaut: json)'
        )
        parser.add_argument(
            '--include-related',
            action='store_true',
            help='Inclure les données liées (Service, Site, Société)'
        )
        parser.add_argument(
            '--natural-keys',
            action='store_true',
            help='Utiliser les clés naturelles'
        )
        parser.add_argument(
            '--service',
            type=str,
            help='Filtrer par nom de service'
        )
        parser.add_argument(
            '--site',
            type=str,
            help='Filtrer par nom de site'
        )
        parser.add_argument(
            '--no-interim',
            action='store_true',
            help='Exclure les intérimaires'
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Afficher les statistiques détaillées'
        )
    
    def handle(self, *args, **options):
        # Construction de la requête
        queryset = Conducteur.actifs.all()
        
        # Filtres optionnels
        if options['service']:
            queryset = queryset.filter(service__nom__icontains=options['service'])
            self.stdout.write(f"📍 Filtre service: {options['service']}")
        
        if options['site']:
            queryset = queryset.filter(site__nom__icontains=options['site'])
            self.stdout.write(f"📍 Filtre site: {options['site']}")
        
        if options['no_interim']:
            queryset = queryset.filter(interim_p=False)
            self.stdout.write("📍 Exclusion des intérimaires")
        
        # Optimisation avec select_related
        queryset = queryset.select_related('service', 'site', 'societe')
        
        # Comptage
        total_conducteurs = queryset.count()
        
        if total_conducteurs == 0:
            self.stdout.write(
                self.style.WARNING('⚠️  Aucun conducteur trouvé avec ces critères')
            )
            return
        
        self.stdout.write(f"📊 {total_conducteurs} conducteurs actifs trouvés")
        
        # Affichage des statistiques si demandé
        if options['stats']:
            self.afficher_statistiques(queryset)
        
        # Préparation des données pour sérialisation
        donnees_a_serialiser = list(queryset)
        
        # Ajout des données liées si demandé
        if options['include_related']:
            # Récupérer tous les services, sites et sociétés liés
            services = set(c.service for c in queryset if c.service)
            sites = set(c.site for c in queryset if c.site)
            societes = set(c.societe for c in queryset if c.societe)
            
            donnees_a_serialiser.extend(services)
            donnees_a_serialiser.extend(sites)
            donnees_a_serialiser.extend(societes)
            
            self.stdout.write(f"📎 Données liées incluses: {len(services)} services, {len(sites)} sites, {len(societes)} sociétés")
        
        # Sérialisation
        try:
            data = serializers.serialize(
                options['format'], 
                donnees_a_serialiser,
                indent=2,
                use_natural_foreign_keys=options['natural_keys'],
                use_natural_primary_keys=options['natural_keys']
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors de la sérialisation: {e}')
            )
            return
        
        # Écriture du fichier
        try:
            with open(options['output'], 'w', encoding='utf-8') as f:
                f.write(data)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Dump créé avec succès: {options["output"]}'
                )
            )
            self.stdout.write(f'📁 Format: {options["format"]}')
            self.stdout.write(f'📦 {total_conducteurs} conducteurs exportés')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors de l\'écriture: {e}')
            )
    
    def afficher_statistiques(self, queryset):
        """Affiche des statistiques détaillées"""
        self.stdout.write("\n📈 Statistiques détaillées:")
        self.stdout.write("=" * 40)
        
        # Par service
        services_stats = {}
        for conducteur in queryset:
            service = conducteur.service.nom if conducteur.service else 'Sans service'
            services_stats[service] = services_stats.get(service, 0) + 1
        
        self.stdout.write("🏢 Répartition par service:")
        for service, count in sorted(services_stats.items()):
            self.stdout.write(f"   • {service}: {count}")
        
        # Par site
        sites_stats = {}
        for conducteur in queryset:
            site = f"{conducteur.site.nom} ({conducteur.site.code_postal})" if conducteur.site else 'Sans site'
            sites_stats[site] = sites_stats.get(site, 0) + 1
        
        self.stdout.write("\n📍 Répartition par site:")
        for site, count in sorted(sites_stats.items()):
            self.stdout.write(f"   • {site}: {count}")
        
        # Intérimaires
        interim_count = queryset.filter(interim_p=True).count()
        permanent_count = queryset.filter(interim_p=False).count()
        
        self.stdout.write(f"\n👥 Types de contrat:")
        self.stdout.write(f"   • Permanents: {permanent_count}")
        self.stdout.write(f"   • Intérimaires: {interim_count}")
        
        # Ancienneté moyenne
        try:
            today = date.today()
            anciennetes = [(today - c.date_entree).days for c in queryset if c.date_entree]
            if anciennetes:
                anciennete_moyenne = sum(anciennetes) / len(anciennetes)
                self.stdout.write(f"\n⏰ Ancienneté moyenne: {anciennete_moyenne:.0f} jours ({anciennete_moyenne/365:.1f} ans)")
        except Exception:
            pass
        
        self.stdout.write("=" * 40)
