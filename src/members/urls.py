from django.urls import path
from members.views import (MemberDetailView, MemberListView,
                           SecurityCreateView, SecurityDetailView)

app_name = "members"
urlpatterns = [
    path("", MemberListView.as_view(), name="members"),
    path("<int:pk>/", MemberDetailView.as_view(), name="member"),
    # path("security/",SecurityCreateView.as_view(),name="security_create"),
    # path("security/",SecurityDetailView.as_view(),name="security_detail"),
]
