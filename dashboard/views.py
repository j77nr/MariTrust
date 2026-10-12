from django.views.generic import TemplateView

from accounts.mixins import RoleRequiredMixin


class EspaceDeclarant(RoleRequiredMixin, TemplateView):
    roles = ["declarant"]
    template_name = "dashboard/declarant.html"


class EspaceAgent(RoleRequiredMixin, TemplateView):
    roles = ["agent", "admin"]
    template_name = "dashboard/agent.html"


class EspaceAdmin(RoleRequiredMixin, TemplateView):
    roles = ["admin"]
    template_name = "dashboard/admin.html"
