from rest_framework import serializers
from insurances.models import Insurance


class InsuranceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Insurance
        fields = '__all__'
        read_only_fields = ('id',)