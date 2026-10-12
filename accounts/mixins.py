from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Limite l'accès d'une vue à un ou plusieurs rôles (ex: roles = ['agent'])."""
    roles = []

    def test_func(self):
        return self.request.user.role in self.roles
