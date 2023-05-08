from django.urls import path

from . import views

app_name = "pr"
urlpatterns = [
    path("", views.index, name="index"),
    path("add_dummy", views.add_dummy, name="add_dummy"),
    path("<str:person_id>/", views.person, name="person"),
]
