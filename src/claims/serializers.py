from rest_framework import serializers

from claims.models import Claim, AddDocument
from members.models import Member

from members.serializers import MemberSerializer

class ClaimSerializer(serializers.ModelSerializer):
    member = MemberSerializer(read_only=True)  # ✅ GET 요청 시 멤버 정보 포함
    member_id = serializers.PrimaryKeyRelatedField(
        queryset=Member.objects.all(), write_only=True, source="member"
    )  # ✅ POST 요청 시 member ID 저장

    class Meta:
        model = Claim
        fields = '__all__'  # ✅ 모든 필드 포함
        read_only_fields = ('id',)



class ClaimAddDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddDocument
        fields = '__all__'