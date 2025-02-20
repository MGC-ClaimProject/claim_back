from claims.views import (ClaimAddDocumentConvertFaxView,
                          ClaimAddDocumentEditFaxView, ClaimDetailDestroyView,
                          ClaimListCreateView, ClaimListUserView, ClaimSendView)
from django.urls import path

app_name = "claims"
urlpatterns = [
    path("", ClaimListUserView.as_view(), name="claims-user"),
    path("<int:pk>/", ClaimListCreateView.as_view(), name="claim-list-create"),
    path(
        "<int:pk>/claim/", ClaimDetailDestroyView.as_view(), name="claim-detail-destroy"
    ),
    path(
        "<int:claim_id>/documents/",
        ClaimAddDocumentConvertFaxView.as_view(),
        name="claim-add-document",
    ),
    path(
        "<int:claim_id>/documents/<int:pk>/",
        ClaimAddDocumentEditFaxView.as_view(),
        name="claim-document-edit",
    ),
    path(
        "<int:claim_id>/send/",
        ClaimSendView.as_view(),
        name="claim-send",
    ),
]
