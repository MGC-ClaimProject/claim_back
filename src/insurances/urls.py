from django.urls import path
from insurances.views import (InsuranceDetailView, InsuranceListView,
                              UpdateMemberInsurancesView)

app_name = "insurances"
urlpatterns = [
    path("<int:pk>/", InsuranceListView.as_view(), name="insurances"),
    path(
        "<int:pk>/insurance/", InsuranceDetailView.as_view(), name="insurances-detail"
    ),
    path(
        "update/<int:member_id>/",
        UpdateMemberInsurancesView.as_view(),
        name="update-member-insurances",
    ),
]
