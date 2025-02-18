from django.urls import path
from users.views.user_views import UserAPIView, UserDeactivateAPIView

app_name = "user"
urlpatterns = [
    path("", UserAPIView.as_view(), name="myinfo"),
    path(
        "deactivate/",
        UserDeactivateAPIView.as_view(),
        name="myinfo_deactivate",
    ),
]
