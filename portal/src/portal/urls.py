from django.urls import path, include

import portal.views.pr
import portal.views.enrollment
import portal.views.osia

pr_patterns = ([
    path("", portal.views.pr.index, name="index"),
    path("portrait/<str:person_id>/<str:identity_id>/", portal.views.pr.portrait, name="portrait"),
    path("portrait-image/<str:person_id>/<str:identity_id>/", portal.views.pr.portrait_image, name="portrait-image"),
    path("add_dummy", portal.views.pr.add_dummy, name="add_dummy"),
    path("<str:person_id>/", portal.views.pr.person, name="person"),
],
"pr",
)

enrollment_patterns = ([
    path("", portal.views.enrollment.index, name="index"),
    path("portrait-image/<str:enrollment_id>/", portal.views.enrollment.portrait_image, name="portrait-image"),
],
"enrollment",
)

osia_patterns = ([
    path("", portal.views.osia.index, name="index"),
],
"osia",
)

urlpatterns = [
    path("enrollment/", include(enrollment_patterns, namespace="enrollment")),
    path("osia/", include(osia_patterns, namespace="osia")),
    path("pr/", include(pr_patterns, namespace="pr")),
]
