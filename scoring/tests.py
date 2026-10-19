from django.test import TestCase

from scoring.models import Critere


class CritereCodeTests(TestCase):
    """Vérifie que le champ 'code' unique existe et est utilisé par seed_demo."""

    def test_code_est_un_champ_unique(self):
        """Le champ code doit être unique et slugifié."""
        field = Critere._meta.get_field("code")
        self.assertTrue(field.unique)

    def test_seed_demo_popule_les_codes(self):
        """Après seed, chaque critère a son code associé."""
        from io import StringIO
        from django.core.management import call_command
        call_command("seed_demo", stdout=StringIO())

        for nom, code_attendu in [
            ("Poids incohérent avec le type de conteneur", "poids_conteneur"),
            ("Marchandise sensible", "marchandise_sensible"),
            ("Marchandise inhabituelle pour la route", "route_inhabituelle"),
            ("Valeur déclarée très inférieure au marché", "valeur_sous_evaluee"),
            ("Escale dans un port à risque (par port)", "port_a_risque"),
            ("Changement de pavillon récent", "pavillon_recent"),
            ("Infractions passées du navire (par infraction)", "infractions_navire"),
            ("Anomalie du signal AIS", "anomalie_ais"),
            ("Opérateur inconnu", "operateur_inconnu"),
            ("Déclaration trop proche de l'arrivée", "declaration_tardive"),
            ("Documents incohérents entre eux", "documents_incoherents"),
            ("Moyen de paiement atypique", "paiement_atypique"),
        ]:
            critere = Critere.objects.get(nom=nom)
            self.assertEqual(critere.code, code_attendu)
