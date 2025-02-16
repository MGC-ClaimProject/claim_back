from django.urls import path

from claims.views import ClaimListUserView, ClaimListCreateView, ClaimDetailDestroyView, ClaimAddDocumentConvertFaxView, \
    ClaimAddDocumentEditFaxView

app_name = "claims"
urlpatterns = [
    path("", ClaimListUserView.as_view(), name="claims-user"),
    path("<int:pk>/", ClaimListCreateView.as_view(), name="claim-list-create"),
    path("member/<int:pk>/", ClaimDetailDestroyView.as_view(), name="claim-detail-destroy"),
    path("<int:claim_id>/documents/", ClaimAddDocumentConvertFaxView.as_view(), name="claim-add-document"),
    path("<int:claim_id>/documents/<int:pk>", ClaimAddDocumentEditFaxView.as_view(), name="claim-document-edit"),
]
