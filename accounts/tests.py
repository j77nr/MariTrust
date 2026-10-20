from django.test import TestCase
from django.urls import reverse

from .models import Utilisateur


class ConnexionTests(TestCase):
    def test_login_est_accessible_sans_authentification_et_sans_identifiants_pre_remplis(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password"')
        self.assertNotContains(response, 'value="agent@maritrust.demo"')
        self.assertNotContains(response, 'value="maritrust2026"')
        self.assertNotContains(response, "Profil de démonstration")
        self.assertNotContains(response, "Connexion chiffrée et auditée")

    def test_connexion_conserve_la_redirection_existante_par_role(self):
        utilisateur = Utilisateur.objects.create_user(
            username="agent-test", password="MariTrust-test-2026", role="agent"
        )

        response = self.client.post(
            reverse("login"),
            {"username": utilisateur.username, "password": "MariTrust-test-2026"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("accueil"))
