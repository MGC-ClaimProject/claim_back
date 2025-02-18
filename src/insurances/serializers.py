from insurances.models import Insurance
from rest_framework import serializers


class InsuranceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Insurance
        fields = "__all__"
        read_only_fields = ("id",)
