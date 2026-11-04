from django.urls import path, include

import portal.views.pr

pr_patterns = ([
    path("", portal.views.pr.index, name="index"),
    path("portrait/<str:person_id>/<str:identity_id>/", portal.views.pr.portrait, name="portrait"),
    path("portrait-image/<str:person_id>/<str:identity_id>/", portal.views.pr.portrait_image, name="portrait-image"),
    path("add_dummy", portal.views.pr.add_dummy, name="add_dummy"),
    path("<str:person_id>/", portal.views.pr.person, name="person"),
],
"pr",
)


urlpatterns = [
    path("pr/", include(pr_patterns, namespace="pr"))
]
