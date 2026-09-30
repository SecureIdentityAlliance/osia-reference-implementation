from django.urls import path

from . import views

app_name = "pr"
urlpatterns = [
    path("", views.index, name="index"),
    path("portrait/<str:person_id>/", views.portrait, name="portrait"),
    path("portrait-image/<str:person_id>/", views.portrait_image, name="portrait-image"),
    path("add_dummy", views.add_dummy, name="add_dummy"),
    path("<str:person_id>/", views.person, name="person"),
]
