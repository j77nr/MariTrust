from django.urls import path

from . import views

app_name = "declarations"

urlpatterns = [
    path("mes-declarations/", views.mes_declarations, name="mes_declarations"),
    path("mes-declarations/nouvelle/", views.creer_declaration, name="creer_declaration"),
]