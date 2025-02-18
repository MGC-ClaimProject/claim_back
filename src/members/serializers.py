from members.models import Member, Security
from rest_framework import serializers


class MemberSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Member
        fields = "__all__"
        read_only_fields = ("user",)


class SecuritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Security
        fields = "__all__"
        read_only_fields = ("id",)
