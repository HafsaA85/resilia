from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path("admin/", admin.site.urls),

    # your custom login
    path("login/", LoginView.as_view(template_name="login.html"), name="login"),

    # Django auth (password reset etc.)
    path("accounts/", include("django.contrib.auth.urls")),

    # your app
    path("", include("resilia.urls")),
    
]