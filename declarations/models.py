import uuid

from django.conf import settings
from django.db import models


class Navire(models.Model):
    """Référentiel des navires. Conserve un historique propre à chaque
    navire (infractions, changement de pavillon), réutilisé comme critère
    de scoring pour toutes ses futures déclarations."""

    class StatutAIS(models.TextChoices):
        NORMAL = "normal", "Normal"
        ANOMALIE = "anomalie", "Anomalie détectée"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=150)
    numero_imo = models.CharField(
        "Numéro IMO", max_length=10, unique=True,
        help_text="Identifiant international unique du navire (7 chiffres)."
    )
    pavillon_actuel = models.CharField(max_length=100)
    date_changement_pavillon = models.DateField(null=True, blank=True)
    nb_infractions_historique = models.PositiveIntegerField(default=0)
    statut_ais = models.CharField(max_length=20, choices=StatutAIS.choices, default=StatutAIS.NORMAL)

    class Meta:
        verbose_name = "Navire"
        verbose_name_plural = "Navires"
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} (IMO {self.numero_imo})"


class Operateur(models.Model):
    """Référentiel des opérateurs économiques (exportateurs/importateurs)."""

    class Statut(models.TextChoices):
        CONNU = "connu", "Connu / enregistré"
        INCONNU = "inconnu", "Inconnu / non enregistré"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=150)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.INCONNU)
    date_premiere_transaction = models.DateField(null=True, blank=True)
    nb_infractions = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Opérateur"
        verbose_name_plural = "Opérateurs"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class PortEscale(models.Model):
    """Référentiel des ports, avec leur niveau de risque propre.
    Modifiable par l'administrateur sans intervention sur le code."""

    class NiveauRisque(models.TextChoices):
        FAIBLE = "faible", "Faible"
        MOYEN = "moyen", "Moyen"
        ELEVE = "eleve", "Élevé"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=150)
    pays = models.CharField(max_length=100)
    niveau_risque = models.CharField(max_length=20, choices=NiveauRisque.choices, default=NiveauRisque.FAIBLE)

    class Meta:
        verbose_name = "Port d'escale"
        verbose_name_plural = "Ports d'escale"
        ordering = ["pays", "nom"]
        unique_together = ("nom", "pays")

    def __str__(self):
        return f"{self.nom} ({self.pays})"


class Declaration(models.Model):
    """Entité centrale du système : une déclaration anticipée de cargaison,
    porteuse du résultat du scoring (score, niveau de risque, statut)."""

    class MoyenPaiement(models.TextChoices):
        VIREMENT = "virement", "Virement bancaire"
        ESPECES = "especes", "Espèces"
        AUTRE = "autre", "Autre"

    class NiveauRisque(models.TextChoices):
        FAIBLE = "faible", "Faible"
        MOYEN = "moyen", "Moyen"
        ELEVE = "eleve", "Élevé"

    class StatutTraitement(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente"
        EN_COURS = "en_cours", "En cours d'analyse"
        TRAITE = "traite", "Traité"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    declarant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="declarations_soumises",
        limit_choices_to={"role": "declarant"},
    )
    navire = models.ForeignKey(Navire, on_delete=models.PROTECT, related_name="declarations")
    operateur = models.ForeignKey(Operateur, on_delete=models.PROTECT, related_name="declarations")
    ports_escale = models.ManyToManyField(
        PortEscale, through="DeclarationPortEscale", related_name="declarations"
    )

    type_marchandise = models.CharField(max_length=150)
    poids_declare_kg = models.DecimalField(max_digits=10, decimal_places=2)
    type_conteneur = models.CharField(max_length=50)
    valeur_declaree = models.DecimalField(max_digits=14, decimal_places=2)
    valeur_marche_reference = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    moyen_paiement = models.CharField(max_length=20, choices=MoyenPaiement.choices)

    date_declaration = models.DateTimeField(auto_now_add=True)
    date_arrivee_prevue = models.DateTimeField()

    # Champs renseignés automatiquement par le moteur de scoring (voir scoring/services.py)
    score = models.PositiveIntegerField(default=0)
    niveau_risque = models.CharField(
        max_length=20, choices=NiveauRisque.choices, default=NiveauRisque.FAIBLE
    )
    statut_traitement = models.CharField(
        max_length=20, choices=StatutTraitement.choices, default=StatutTraitement.EN_ATTENTE
    )

    class Meta:
        verbose_name = "Déclaration"
        verbose_name_plural = "Déclarations"
        ordering = ["-date_declaration"]
        indexes = [
            models.Index(fields=["niveau_risque", "statut_traitement"]),
            models.Index(fields=["-date_declaration"]),
        ]

    def __str__(self):
        return f"Déclaration {self.id} — {self.navire.nom} ({self.get_niveau_risque_display()})"


class DeclarationPortEscale(models.Model):
    """Table pivot (classe d'association) entre Declaration et PortEscale.
    Porte un attribut propre à la combinaison : l'ordre de passage du port
    dans le trajet du navire."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    declaration = models.ForeignKey(Declaration, on_delete=models.CASCADE)
    port_escale = models.ForeignKey(PortEscale, on_delete=models.PROTECT)
    ordre_passage = models.PositiveSmallIntegerField(
        help_text="Position du port dans le trajet (1 = escale la plus ancienne)."
    )

    class Meta:
        verbose_name = "Port d'escale de la déclaration"
        verbose_name_plural = "Ports d'escale des déclarations"
        ordering = ["declaration", "ordre_passage"]
        unique_together = ("declaration", "ordre_passage")

    def __str__(self):
        return f"{self.declaration_id} — escale {self.ordre_passage}: {self.port_escale.nom}"


class HistoriqueTraitement(models.Model):
    """Journal d'audit : trace chaque action effectuée par un agent sur
    une déclaration (prise en charge, clôture, commentaire...)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    declaration = models.ForeignKey(
        Declaration, on_delete=models.CASCADE, related_name="historique"
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="actions_effectuees",
        limit_choices_to={"role": "agent"},
    )
    action = models.CharField(max_length=100)
    commentaire = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Historique de traitement"
        verbose_name_plural = "Historiques de traitement"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date:%d/%m/%Y %H:%M} — {self.agent} — {self.action}"
