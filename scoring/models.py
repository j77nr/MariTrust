import uuid

from django.db import models

from declarations.models import Declaration


class Critere(models.Model):
    """Référentiel des critères de risque, paramétrable par l'administrateur
    sans modification du code (nom, poids, activation)."""

    class Categorie(models.TextChoices):
        CARGAISON = "cargaison", "Cargaison"
        NAVIRE = "navire", "Navire"
        OPERATEUR = "operateur", "Opérateur"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.SlugField(unique=True, help_text="Identifiant stable du critère (ex: poids_conteneur).")
    nom = models.CharField(max_length=150)
    categorie = models.CharField(max_length=20, choices=Categorie.choices)
    poids = models.PositiveIntegerField(help_text="Points attribués lorsque ce critère se déclenche.")
    actif = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Critère de scoring"
        verbose_name_plural = "Critères de scoring"
        ordering = ["categorie", "-poids"]

    def __str__(self):
        return f"{self.nom} (+{self.poids})"


class ScoreDetail(models.Model):
    """Décompose le score d'une déclaration critère par critère, pour
    garantir la transparence du calcul (quel critère a rapporté combien
    de points, affiché à l'agent dans le détail du dossier)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    declaration = models.ForeignKey(
        Declaration, on_delete=models.CASCADE, related_name="score_details"
    )
    critere = models.ForeignKey(
        Critere, on_delete=models.PROTECT, related_name="occurrences"
    )
    points_attribues = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Détail de score"
        verbose_name_plural = "Détails de score"
        unique_together = ("declaration", "critere")

    def __str__(self):
        return f"{self.declaration_id} — {self.critere.nom}: +{self.points_attribues}"
