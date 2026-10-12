from django.contrib import admin

from .models import Critere, ScoreDetail


@admin.register(Critere)
class CritereAdmin(admin.ModelAdmin):
    list_display = ("nom", "categorie", "poids", "actif")
    list_editable = ("poids", "actif")
    list_filter = ("categorie", "actif")


admin.site.register(ScoreDetail)
