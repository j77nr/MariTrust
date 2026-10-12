from django.urls import path

from . import views

urlpatterns = [
    path("declarant/", views.EspaceDeclarant.as_view(), name="espace_declarant"),
    path("agent/", views.EspaceAgent.as_view(), name="espace_agent"),
    path("administration/", views.EspaceAdmin.as_view(), name="espace_admin"),
]
