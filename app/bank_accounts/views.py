from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated
from bank_accounts.models import CardAccountModel, TransactionModel
from bank_accounts.serializers import CardAccountSerializer, TransactionSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter


class CardAccountViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CardAccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CardAccountModel.objects.filter(user=self.request.user)

    @extend_schema(
        parameters=[
            OpenApiParameter(name='card_number', required=True, type=str,
                             location=OpenApiParameter.QUERY, description='Номер карты')
        ],
        responses={200: CardAccountSerializer}
    )
    @action(detail=False, methods=["get"], url_path="by-number")
    def get_by_card_number(self, request):
        card_number = request.query_params.get("card_number")
        if not card_number:
            return Response({"detail": "Номер карты не передан."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            card = CardAccountModel.objects.get(card_number=card_number)
        except CardAccountModel.DoesNotExist:
            return Response({"detail": "Карта не найдена."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CardAccountSerializer(card)
        return Response(serializer.data)


class TransactionListCreateView(generics.ListCreateAPIView):
    queryset = TransactionModel.objects.all()
    serializer_class = TransactionSerializer


class TransactionDetailView(generics.RetrieveAPIView):
    queryset = TransactionModel.objects.all()
    serializer_class = TransactionSerializer
