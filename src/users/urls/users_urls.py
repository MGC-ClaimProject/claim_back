from django.urls import path
from users.views.oauth_views import (KakaoLoginCallbackView, LogoutView,
                                     RefreshAccessTokenAPIView)

app_name = "users"
urlpatterns = [
    path(
        "login/kakao/callback/", KakaoLoginCallbackView.as_view(), name="kakao_callback"
    ),
    path("token/refresh/", RefreshAccessTokenAPIView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
