"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (SpectacularAPIView, SpectacularRedocView,
                                   SpectacularSwaggerView)

base_url = "api/v1"

urlpatterns = [
    path(f"{base_url}/admin/", admin.site.urls),
    path(f"{base_url}/user/", include("users.urls.user_urls")),
    path(f"{base_url}/users/", include("users.urls.users_urls")),
    path(f"{base_url}/members/", include("members.urls")),
    path(f"{base_url}/insurances/", include("insurances.urls")),
    path(f"{base_url}/claims/", include("claims.urls")),
]

if settings.DEBUG:
    urlpatterns += [
        path(f"{base_url}/schema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            f"{base_url}/schema/swagger-ui/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
        path(
            f"{base_url}/schema/redoc/",
            SpectacularRedocView.as_view(url_name="schema"),
            name="redoc",
        ),
    ]
