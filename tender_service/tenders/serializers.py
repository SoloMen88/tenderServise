from rest_framework import serializers
from .models import Organization, Employee, Tender, Bid, Review


class TenderSerializer(serializers.ModelSerializer):
    """Сериализатор для модели тендера.
    Переопределяет название некоторых полей, скрывает поле creatorUsername."""

    organizationId = serializers.PrimaryKeyRelatedField(
        many=False, read_only=True)
    organizationId = serializers.CharField(source='organization_id')
    serviceType = serializers.CharField(source='service_type')
    creatorUsername = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(),
        write_only=True,
        source='creator_id'
    )

    class Meta:
        model = Tender
        fields = ('id', 'name', 'description', 'serviceType', 'status', 'organizationId',
                  'version', 'createdAt', 'creatorUsername')


class BidSerializer(serializers.ModelSerializer):
    """Сериализатор для модели предложения.
    Переопределяет название некоторых полей, скрывает 
    поля creatorUsername и creatorUsername."""

    authorId = serializers.PrimaryKeyRelatedField(
        many=False, read_only=True)
    creatorUsername = serializers.CharField(source='creator_id')
    authorId = serializers.CharField(source='creator_id')
    tenderId = serializers.PrimaryKeyRelatedField(
        queryset=Tender.objects.all(),
        source='tender'
    )
    creatorUsername = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(),
        write_only=True,
        source='creator'
    )
    organizationId = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(),
        write_only=True,
        source='organization'
    )

    class Meta:
        model = Bid
        fields = ('id', 'name', 'description', 'status', 'tenderId', 'authorType', 'authorId',
                  'version', 'createdAt', 'creatorUsername', 'organizationId')


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ('id', 'description', 'createdAt')
