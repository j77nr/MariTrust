import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class Utilisateur(AbstractUser):
    """
    Étend AbstractUser pour bénéficier du système d'authentification natif
    de Django (hash de mot de passe, gestion des sessions, etc.) tout en
    ajoutant le champ `role`, qui pilote les permissions (RBAC) dans
    l'ensemble de l'application.
    """

    class Role(models.TextChoices):
        DECLARANT = "declarant", "Déclarant"
        AGENT = "agent", "Agent de contrôle"
        ADMIN = "admin", "Administrateur"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.DECLARANT)
    derniere_connexion_ip = models.GenericIPAddressField(null=True, blank=True)

    # Pertinent pour le rôle DECLARANT : l'employé agit au nom d'une société
    # consignataire. On sait ainsi qui a déclaré ET pour quelle société.
    societe = models.ForeignKey(
        "declarations.Operateur",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employes",
        help_text="Société consignataire pour laquelle cet utilisateur agit.",
    )

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    # --- Raccourcis pratiques pour les permissions DRF ---
    @property
    def est_declarant(self):
        return self.role == self.Role.DECLARANT

    @property
    def est_agent(self):
        return self.role == self.Role.AGENT

    @property
    def est_admin(self):
        return self.role == self.Role.ADMIN
