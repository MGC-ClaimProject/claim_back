from claims.models import AddDocument, Claim
from members.models import Member
from members.serializers import MemberSerializer
from rest_framework import serializers


class ClaimAddDocumentSerializer(serializers.ModelSerializer):
    """✅ 문서 정보를 상세하게 반환하는 Serializer"""

    class Meta:
        model = AddDocument
        fields = "__all__"  # ✅ 모든 필드 포함 (id, document_url, created_at, updated_at, page_count 등)


class ClaimSerializer(serializers.ModelSerializer):
    member = MemberSerializer(read_only=True)  # ✅ GET 요청 시 멤버 정보 포함
    member_id = serializers.PrimaryKeyRelatedField(
        queryset=Member.objects.all(), write_only=True, source="member"
    )  # ✅ POST 요청 시 member ID 저장

    documents = ClaimAddDocumentSerializer(
        many=True, read_only=True
    )  # ✅ `source="documents"` 제거

    class Meta:
        model = Claim
        fields = "__all__"  # ✅ 모든 필드 포함
        read_only_fields = ("id",)
