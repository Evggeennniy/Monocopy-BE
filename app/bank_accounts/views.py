from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated
from bank_accounts.models import CardAccountModel, TransactionModel
from bank_accounts.serializers import CardAccountSerializer, TransactionSerializer


class CardAccountViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CardAccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return CardAccountModel.objects.filter(user=user)


class TransactionListCreateView(generics.ListCreateAPIView):
    queryset = TransactionModel.objects.all()
    serializer_class = TransactionSerializer


class TransactionDetailView(generics.RetrieveAPIView):
    queryset = TransactionModel.objects.all()
    serializer_class = TransactionSerializer
