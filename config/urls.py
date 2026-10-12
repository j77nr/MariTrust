from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from accounts.views import accueil

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("connexion/", auth_views.LoginView.as_view(), name="login"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
    path("", accueil, name="accueil"),
    path("", include("declarations.urls")),
    path("", include("dashboard.urls")),
]