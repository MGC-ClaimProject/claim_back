from django.urls import path
from users.views.oauth_views import (LogoutView, RefreshAccessTokenAPIView,
                                     SocialLoginAPIView)
from users.views.user_views import MyInfoAPIView, MyInfoDeactivateAPIView

app_name = "users"
urlpatterns = [
    path(
        "login/<str:provider>/callback/",
        SocialLoginAPIView.as_view(),
        name="social_login",
    ),
    path("token/refresh/", RefreshAccessTokenAPIView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("myinfo/", MyInfoAPIView.as_view(), name="myinfo"),
    path(
        "myinfo/deactivate/",
        MyInfoDeactivateAPIView.as_view(),
        name="myinfo_deactivate",
    ),
]
