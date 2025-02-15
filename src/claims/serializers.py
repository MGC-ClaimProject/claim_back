from rest_framework import serializers

from claims.models import Claim, AddDocument


class ClaimSerializer(serializers.ModelSerializer):

    class Meta:
        model = Claim
        fields = '__all__'
        read_only_fields = ('id',)


class ClaimAddDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddDocument
        fields = '__all__'