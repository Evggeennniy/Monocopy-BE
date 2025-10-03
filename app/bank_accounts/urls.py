from django.urls import path, include
from rest_framework.routers import DefaultRouter
from bank_accounts.views import CardAccountViewSet, TransactionListCreateView, TransactionDetailView

router = DefaultRouter()
router.register(r'cards', CardAccountViewSet, basename="card")

urlpatterns = [
    path("", include(router.urls)),
    path("transactions/", TransactionListCreateView.as_view(), name="transactions"),
    path('transactions/<int:pk>/', TransactionDetailView.as_view(), name='transaction-detail'),
]
