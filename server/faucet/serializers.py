from rest_framework import serializers

class FundRequestSerializer(serializers.Serializer):
    amount = serializers.IntegerField()
