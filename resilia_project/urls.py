from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView
from resilia.views import submit_lead
from django.contrib.auth import views as auth_views


urlpatterns = [
    path("zaynadmin/", admin.site.urls),

    # your custom login
    path("login/", LoginView.as_view(template_name="login.html"), name="login"),

    # Django auth (password reset etc.)
    path("accounts/", include("django.contrib.auth.urls")),

    # your app
    path("", include("resilia.urls")),
    path("api/lead/", submit_lead, name="submit_lead"),
    

    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]
    
