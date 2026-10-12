from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Utilisateur
from .models import Declaration, Navire, Operateur, PortEscale


class DeclarationDeclarantTests(TestCase):
    def setUp(self):
        self.societe = Operateur.objects.create(nom="Consignation A", statut="connu")
        self.autre_societe = Operateur.objects.create(nom="Consignation B", statut="connu")
        self.declarant = Utilisateur.objects.create_user(
            username="declarant-a", password="secret", role="declarant", societe=self.societe
        )
        self.autre_declarant = Utilisateur.objects.create_user(
            username="declarant-b", password="secret", role="declarant", societe=self.autre_societe
        )
        self.navire = Navire.objects.create(nom="Aster", numero_imo="1234567", pavillon_actuel="TG")
        self.port = PortEscale.objects.create(nom="Lomé", pays="Togo")

    def test_creation_rattache_le_declarant_et_sa_societe_et_ordonne_les_escales(self):
        self.client.force_login(self.declarant)
        data = {
            "navire": self.navire.pk,
            "type_marchandise": "Cacao",
            "poids_declare_kg": "1000.00",
            "type_conteneur": "20 pieds",
            "valeur_declaree": "2500.00",
            "moyen_paiement": "virement",
            "date_arrivee_prevue": (timezone.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M"),
            "declarationportescale_set-TOTAL_FORMS": "10",
            "declarationportescale_set-INITIAL_FORMS": "0",
            "declarationportescale_set-MIN_NUM_FORMS": "0",
            "declarationportescale_set-MAX_NUM_FORMS": "10",
            "declarationportescale_set-0-port_escale": self.port.pk,
        }
        response = self.client.post(reverse("declarations:creer_declaration"), data)

        self.assertRedirects(response, reverse("declarations:mes_declarations"))
        declaration = Declaration.objects.get()
        self.assertEqual(declaration.declarant, self.declarant)
        self.assertEqual(declaration.operateur, self.societe)
        self.assertEqual(declaration.declarationportescale_set.get().ordre_passage, 1)

    def test_liste_est_filtre_par_utilisateur_connecte_et_n_expose_pas_le_score(self):
        Declaration.objects.create(
            declarant=self.declarant, navire=self.navire, operateur=self.societe,
            type_marchandise="Cacao", poids_declare_kg=1000, type_conteneur="20 pieds",
            valeur_declaree=2500, moyen_paiement="virement",
            date_arrivee_prevue=timezone.now() + timedelta(days=2), score=95,
        )
        Declaration.objects.create(
            declarant=self.autre_declarant, navire=self.navire, operateur=self.autre_societe,
            type_marchandise="Poivre", poids_declare_kg=500, type_conteneur="20 pieds",
            valeur_declaree=1200, moyen_paiement="virement",
            date_arrivee_prevue=timezone.now() + timedelta(days=2), score=10,
        )
        self.client.force_login(self.declarant)

        response = self.client.get(reverse("declarations:mes_declarations"))

        self.assertContains(response, "Cacao")
        self.assertNotContains(response, "Poivre")
        self.assertNotContains(response, "95")

    def test_declarant_sans_societe_est_refuse(self):
        sans_societe = Utilisateur.objects.create_user(
            username="sans-societe", password="secret", role="declarant"
        )
        self.client.force_login(sans_societe)

        response = self.client.get(reverse("declarations:creer_declaration"))

        self.assertEqual(response.status_code, 403)