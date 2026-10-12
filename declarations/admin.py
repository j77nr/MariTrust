from django.contrib import admin

from .models import Declaration, DeclarationPortEscale, HistoriqueTraitement, Navire, Operateur, PortEscale


class PortInline(admin.TabularInline):
    model = DeclarationPortEscale
    extra = 0


@admin.register(Declaration)
class DeclarationAdmin(admin.ModelAdmin):
    list_display = ("id", "navire", "operateur", "score", "niveau_risque", "statut_traitement", "date_declaration")
    list_filter = ("niveau_risque", "statut_traitement")
    inlines = [PortInline]


admin.site.register([Navire, Operateur, PortEscale, HistoriqueTraitement])
