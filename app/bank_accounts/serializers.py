from rest_framework import serializers
from django.db import models
from django.contrib.auth.models import User
from bank_accounts.models import CardAccountModel, TransactionModel


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionModel
        fields = "__all__"
        read_only_fields = ("operation_type", "timestamp", "balance_after")

    def create(self, validated_data):
        amount = validated_data.get("amount")
        from_card = validated_data.get("from_card")
        to_card_number = validated_data.get("to_card")

        if amount <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")

        to_card = CardAccountModel.objects.filter(card_number=to_card_number).first()
        if to_card:
            to_card.balance += amount
            to_card.save()

        from_card_acc = CardAccountModel.objects.filter(card_number=from_card).first()
        if from_card_acc:
            if from_card_acc.balance < amount:
                raise serializers.ValidationError("Insufficient funds for withdrawal.")
            from_card_acc.balance -= amount
            from_card_acc.save()

        return TransactionModel.objects.create(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name"]


class CardAccountSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    transactions = serializers.SerializerMethodField()

    class Meta:
        model = CardAccountModel
        fields = [
            "id", "user", "card_number",
            "expiration_date", "balance", "transactions"
        ]

    def get_user(self, obj):
        return UserSerializer(obj.user).data

    def get_transactions(self, obj):
        transactions = TransactionModel.objects.filter(
            models.Q(from_card=obj.card_number) | models.Q(to_card=obj.card_number)
        )
        return TransactionSerializer(transactions, many=True).data
