from django.core.management.base import BaseCommand

from accounts.models import Utilisateur
from declarations.models import Operateur, PortEscale
from scoring.models import Critere

CRITERES = [
    ("Poids incohérent avec le type de conteneur", "poids_conteneur", "cargaison", 25),
    ("Marchandise sensible", "marchandise_sensible", "cargaison", 20),
    ("Marchandise inhabituelle pour la route", "route_inhabituelle", "cargaison", 15),
    ("Valeur déclarée très inférieure au marché", "valeur_sous_evaluee", "cargaison", 15),
    ("Escale dans un port à risque (par port)", "port_a_risque", "navire", 15),
    ("Changement de pavillon récent", "pavillon_recent", "navire", 20),
    ("Infractions passées du navire (par infraction)", "infractions_navire", "navire", 10),
    ("Anomalie du signal AIS", "anomalie_ais", "navire", 25),
    ("Opérateur inconnu", "operateur_inconnu", "operateur", 20),
    ("Déclaration trop proche de l'arrivée", "declaration_tardive", "operateur", 15),
    ("Documents incohérents entre eux", "documents_incoherents", "operateur", 25),
    ("Moyen de paiement atypique", "paiement_atypique", "operateur", 15),
]


class Command(BaseCommand):
    help = "Crée des données de démonstration : comptes, société, ports, critères."

    def handle(self, *args, **options):
        societe, _ = Operateur.objects.get_or_create(
            nom="Société Démo Consignation", defaults={"statut": "connu"})
        comptes = [("declarant1", "declarant", societe), ("agent1", "agent", None), ("admin1", "admin", None)]
        for username, role, soc in comptes:
            u, created = Utilisateur.objects.get_or_create(
                username=username, defaults={"role": role, "societe": soc, "is_staff": role == "admin"})
            if created:
                u.set_password("demo1234")
                u.save()
        ports = [("Lomé", "Togo", "faible"), ("Abidjan", "Côte d'Ivoire", "faible"),
                 ("Lagos", "Nigeria", "moyen"), ("Port fictif à risque", "Pays test", "eleve")]
        for nom, pays, risque in ports:
            PortEscale.objects.get_or_create(nom=nom, pays=pays, defaults={"niveau_risque": risque})
        for nom, code, cat, poids in CRITERES:
            Critere.objects.get_or_create(code=code, defaults={"nom": nom, "categorie": cat, "poids": poids})
        self.stdout.write(self.style.SUCCESS("Données de démonstration créées (mot de passe : demo1234)."))
