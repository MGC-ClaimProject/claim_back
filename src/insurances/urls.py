from django.urls import path
from insurances.views import InsuranceListView, InsuranceDetailView

app_name = "insurances"
urlpatterns = [
    path("<int:pk>/", InsuranceListView.as_view(), name="insurances"),
    path("<int:member_id>/<int:pk>", InsuranceDetailView.as_view(), name="insurances-detail"),

]
