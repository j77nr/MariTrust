from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Rôle et société", {"fields": ("role", "societe")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Rôle et société", {"fields": ("role", "societe")}),)
    list_display = ("username", "email", "role", "societe", "is_active")
    list_filter = ("role",)
