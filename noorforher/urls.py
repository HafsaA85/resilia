from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


app_name = "noorforher"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("work-with-me/", views.work_with_me, name="work_with_me"),
    path("terms/", views.terms_of_use, name="terms_of_use"),
    path("privacy/", views.privacy_policy, name="privacy_policy"),

    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("tracker/", views.tracker_list, name="tracker_list"),
    path("tracker/new/", views.tracker_create, name="tracker_create"),
    path("tracker/<int:pk>/edit/", views.tracker_update, name="tracker_update"),

    path("journal/", views.journal_list, name="journal_list"),
    path("journal/new/", views.journal_create, name="journal_create"),
    path(
        "journal/new/<int:trigger_id>/",
        views.journal_create,
        name="journal_create_from_trigger",
    ),
    path("journal/<int:pk>/edit/", views.journal_edit, name="journal_edit"),
    path("journal/<int:pk>/delete/", views.journal_delete, name="journal_delete"),
]
