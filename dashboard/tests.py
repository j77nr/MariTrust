from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Utilisateur
from declarations.models import Declaration, Navire, Operateur, PortEscale
from scoring.models import Critere


class EspaceAgentTests(TestCase):
    def setUp(self):
        self.agent = Utilisateur.objects.create_user(
            username="agent-test", password="Agent-test-2026", role="agent"
        )
        self.admin = Utilisateur.objects.create_user(
            username="admin-test", password="Admin-test-2026", role="admin"
        )
        self.declarant = Utilisateur.objects.create_user(
            username="declarant-test", password="Declarant-test-2026", role="declarant"
        )

    def test_agent_et_admin_peuvent_acceder_a_la_supervision(self):
        for utilisateur in (self.agent, self.admin):
            with self.subTest(role=utilisateur.role):
                self.client.force_login(utilisateur)
                response = self.client.get(reverse("espace_agent"))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Supervision des risques")

    def test_declarant_ne_peut_pas_acceder_a_la_supervision(self):
        self.client.force_login(self.declarant)

        response = self.client.get(reverse("espace_agent"))

        self.assertEqual(response.status_code, 403)

    def test_visiteur_non_connecte_est_redirige_vers_la_connexion(self):
        response = self.client.get(reverse("espace_agent"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_supervision_affiche_les_declarations_reelles_et_ne_change_pas_la_selection(self):
        operateur = Operateur.objects.create(nom="Consignation test", statut="connu")
        navire = Navire.objects.create(
            nom="Aster", numero_imo="9074729", pavillon_actuel="TG"
        )
        port = PortEscale.objects.create(nom="Lomé", pays="Togo", niveau_risque="faible")
        declaration = Declaration.objects.create(
            declarant=self.declarant,
            navire=navire,
            operateur=operateur,
            type_marchandise="Cacao",
            poids_declare_kg=1000,
            type_conteneur="20 pieds",
            valeur_declaree=2500,
            moyen_paiement="virement",
            date_arrivee_prevue=timezone.now() + timedelta(days=2),
            score=73,
            niveau_risque="eleve",
        )
        declaration.ports_escale.add(port, through_defaults={"ordre_passage": 1})
        declaration_recente = Declaration.objects.create(
            declarant=self.declarant,
            navire=Navire.objects.create(
                nom="Atlas", numero_imo="5607310", pavillon_actuel="SN"
            ),
            operateur=operateur,
            type_marchandise="Café",
            poids_declare_kg=1500,
            type_conteneur="40 pieds",
            valeur_declaree=4000,
            moyen_paiement="virement",
            date_arrivee_prevue=timezone.now() + timedelta(days=1),
            score=90,
            niveau_risque="eleve",
        )
        self.client.force_login(self.agent)

        response = self.client.get(
            reverse("espace_agent"), {"declaration": str(declaration.pk)}
        )

        self.assertContains(response, "Aster")
        self.assertContains(response, "Cacao")
        self.assertContains(response, "73")
        self.assertContains(response, "Lomé")
        self.assertContains(response, "Référence lisible indisponible")
        self.assertContains(response, "devise non renseignée")
        self.assertContains(response, "coordonnées des ports non renseignées")
        self.assertEqual(response.context["selected_declaration"], declaration)
        self.assertNotEqual(response.context["selected_declaration"], declaration_recente)


class EspaceDeclarantTests(TestCase):
    def setUp(self):
        self.declarant = Utilisateur.objects.create_user(
            username="declarant-espace", password="Declarant-test-2026", role="declarant"
        )
        self.agent = Utilisateur.objects.create_user(
            username="agent-espace", password="Agent-test-2026", role="agent"
        )
        self.admin = Utilisateur.objects.create_user(
            username="admin-espace", password="Admin-test-2026", role="admin"
        )

    def test_declarant_peut_acceder_a_son_espace_sans_voir_le_score(self):
        operateur = Operateur.objects.create(nom="Consignation espace", statut="connu")
        self.declarant.societe = operateur
        self.declarant.save(update_fields=["societe"])
        navire = Navire.objects.create(
            nom="Aster", numero_imo="9074729", pavillon_actuel="TG"
        )
        Declaration.objects.create(
            declarant=self.declarant,
            navire=navire,
            operateur=operateur,
            type_marchandise="Cacao",
            poids_declare_kg=1000,
            type_conteneur="20 pieds",
            valeur_declaree=2500,
            moyen_paiement="virement",
            date_arrivee_prevue=timezone.now() + timedelta(days=2),
            score=73,
            niveau_risque="eleve",
        )
        self.client.force_login(self.declarant)

        response = self.client.get(reverse("espace_declarant"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aster")
        self.assertContains(response, "Cacao")
        self.assertContains(response, "Mes déclarations")
        self.assertNotContains(response, "score")
        self.assertNotContains(response, "73")
        self.assertNotContains(response, "Élevé")

    def test_agent_et_admin_ne_peuvent_pas_acceder_a_l_espace_declarant(self):
        for utilisateur in (self.agent, self.admin):
            with self.subTest(role=utilisateur.role):
                self.client.force_login(utilisateur)
                response = self.client.get(reverse("espace_declarant"))
                self.assertEqual(response.status_code, 403)

    def test_visiteur_non_connecte_est_redirige_vers_la_connexion(self):
        response = self.client.get(reverse("espace_declarant"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])


class EspaceAdminTests(TestCase):
    def setUp(self):
        self.admin = Utilisateur.objects.create_user(
            username="admin-dashboard", password="Admin-test-2026", role="admin"
        )
        self.agent = Utilisateur.objects.create_user(
            username="agent-dashboard", password="Agent-test-2026", role="agent"
        )
        self.declarant = Utilisateur.objects.create_user(
            username="declarant-dashboard", password="Declarant-test-2026", role="declarant"
        )
        self.critere = Critere.objects.create(
            code="poids_test",
            nom="Poids incohérent",
            categorie="cargaison",
            poids=25,
            description="Poids supérieur à la capacité déclarée.",
        )

    def test_administrateur_peut_acceder_aux_indicateurs_et_modifier_un_critere(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("espace_admin"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Déclarations totales")
        self.assertContains(response, "Poids incohérent")
        self.assertContains(response, "Poids supérieur à la capacité déclarée.")

        response = self.client.post(
            reverse("espace_admin"),
            {
                "criteres-TOTAL_FORMS": "1",
                "criteres-INITIAL_FORMS": "1",
                "criteres-MIN_NUM_FORMS": "0",
                "criteres-MAX_NUM_FORMS": "1000",
                "criteres-0-id": str(self.critere.pk),
                "criteres-0-poids": "42",
                "criteres-0-actif": "on",
            },
        )

        self.assertRedirects(response, reverse("espace_admin"))
        self.critere.refresh_from_db()
        self.assertEqual(self.critere.poids, 42)
        self.assertTrue(self.critere.actif)

    def test_agent_et_declarant_ne_peuvent_pas_acceder_a_l_administration(self):
        for utilisateur in (self.agent, self.declarant):
            with self.subTest(role=utilisateur.role):
                self.client.force_login(utilisateur)
                response = self.client.get(reverse("espace_admin"))
                self.assertEqual(response.status_code, 403)

    def test_visiteur_non_connecte_est_redirige_vers_la_connexion(self):
        response = self.client.get(reverse("espace_admin"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])
