from members.models import Member
from rest_framework import serializers
from users.models import User


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "is_active",
        ]
        read_only_fields = ("id", "email")
