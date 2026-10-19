from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Utilisateur
from .models import Declaration, Navire, Operateur, PortEscale


class DeclarationDeclarantTests(TestCase):
    # IMO valides (checksum OK) :
    # 9074729 -> 9*7+0*6+7*5+4*4+7*3+2*2=139, 139%10=9 ✓
    # 5607310 -> 5*7+6*6+0*5+7*4+3*3+1*2=110, 110%10=0 ✓
    # 9074822 -> 9*7+0*6+7*5+4*4+8*3+2*2=142, 142%10=2 ✓
    # IMO invalide : 9074728 (dernier chiffre 8 ≠ 9)
    IMO_VALIDE_ASTER = "9074729"
    IMO_VALIDE_AUTRE = "5607310"
    IMO_INVALIDE = "9074728"

    def setUp(self):
        self.societe = Operateur.objects.create(nom="Consignation A", statut="connu")
        self.autre_societe = Operateur.objects.create(nom="Consignation B", statut="connu")
        self.declarant = Utilisateur.objects.create_user(
            username="declarant-a", password="secret", role="declarant", societe=self.societe
        )
        self.autre_declarant = Utilisateur.objects.create_user(
            username="declarant-b", password="secret", role="declarant", societe=self.autre_societe
        )
        self.navire = Navire.objects.create(
            nom="Aster", numero_imo=self.IMO_VALIDE_ASTER, pavillon_actuel="TG"
        )
        self.port = PortEscale.objects.create(nom="Lomé", pays="Togo")

    def _donnees_formulaire(self, **overrides):
        """Données de formulaire valides avec les nouveaux champs navire."""
        data = {
            "navire_nom": "Aster",
            "navire_imo": self.IMO_VALIDE_ASTER,
            "navire_pavillon": "TG",
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
        data.update(overrides)
        return data

    def test_creation_rattache_le_declarant_et_sa_societe_et_ordonne_les_escales(self):
        self.client.force_login(self.declarant)
        data = self._donnees_formulaire()
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
            date_arrivee_prevue=timezone.now() + timedelta(days=2), score=73,
            niveau_risque="eleve"
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
        self.assertNotContains(response, "73")
        self.assertNotContains(response, "Élevé")
        self.assertNotContains(response, "score")

    def test_declarant_sans_societe_est_refuse(self):
        sans_societe = Utilisateur.objects.create_user(
            username="sans-societe", password="secret", role="declarant"
        )
        self.client.force_login(sans_societe)

        response = self.client.get(reverse("declarations:creer_declaration"))

        self.assertEqual(response.status_code, 403)

    def test_navire_inconnu_est_cree_apres_depot(self):
        self.client.force_login(self.declarant)
        data = self._donnees_formulaire(
            navire_nom="Nouveau Navire",
            navire_imo=self.IMO_VALIDE_AUTRE,
            navire_pavillon="SN"
        )
        response = self.client.post(reverse("declarations:creer_declaration"), data)

        self.assertRedirects(response, reverse("declarations:mes_declarations"))
        self.assertEqual(Navire.objects.count(), 2)
        nouveau = Navire.objects.get(numero_imo=self.IMO_VALIDE_AUTRE)
        self.assertEqual(nouveau.nom, "Nouveau Navire")
        self.assertEqual(nouveau.pavillon_actuel, "SN")

    def test_navire_connu_non_recree_apres_deux_declarations(self):
        self.client.force_login(self.declarant)
        data1 = self._donnees_formulaire()
        self.client.post(reverse("declarations:creer_declaration"), data1)
        data2 = self._donnees_formulaire()
        self.client.post(reverse("declarations:creer_declaration"), data2)

        self.assertEqual(Navire.objects.count(), 1)

    def test_navire_existant_non_modifie_si_nom_different(self):
        self.client.force_login(self.declarant)
        data = self._donnees_formulaire(
            navire_nom="Nom Totalement Different",
            navire_pavillon="FR"
        )
        response = self.client.post(reverse("declarations:creer_declaration"), data)

        self.assertRedirects(response, reverse("declarations:mes_declarations"))
        aster = Navire.objects.get(numero_imo=self.IMO_VALIDE_ASTER)
        self.assertEqual(aster.nom, "Aster")
        self.assertEqual(aster.pavillon_actuel, "TG")
        self.assertEqual(Navire.objects.count(), 1)

    def test_imo_invalide_est_refuse(self):
        self.client.force_login(self.declarant)
        data = self._donnees_formulaire(navire_imo=self.IMO_INVALIDE)
        response = self.client.post(reverse("declarations:creer_declaration"), data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "chiffre de contrôle")
        self.assertEqual(Navire.objects.count(), 1)
        self.assertEqual(Declaration.objects.count(), 0)

    def test_navire_inconnu_avec_pavillon_vide_est_refuse(self):
        """IMO valide mais pavillon vide pour un navire inconnu → refusé, pas de création."""
        self.client.force_login(self.declarant)
        count_avant = Navire.objects.count()
        data = self._donnees_formulaire(
            navire_nom="Nouveau Sans Pavillon",
            navire_imo=self.IMO_VALIDE_AUTRE,
            navire_pavillon=""
        )
        response = self.client.post(reverse("declarations:creer_declaration"), data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "pavillon")
        self.assertEqual(Navire.objects.count(), count_avant)  # pas de création
        self.assertEqual(Declaration.objects.count(), 0)