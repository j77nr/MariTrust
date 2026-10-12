from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
def accueil(request):
    """Envoie chaque utilisateur vers son espace selon son rôle."""
    cibles = {"declarant": "espace_declarant", "agent": "espace_agent", "admin": "espace_admin"}
    return redirect(cibles.get(request.user.role, "login"))
