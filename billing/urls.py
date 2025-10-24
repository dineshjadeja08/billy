from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CorporateAccountViewSet,
    DailyReportView,
    DiscountViewSet,
    FolioViewSet,
    GuestViewSet,
    InvoiceViewSet,
    OutstandingReportView,
    PMSWebhookView,
    POSWebhookView,
    PaymentGatewayWebhookView,
    PaymentMethodViewSet,
    PaymentViewSet,
    ReservationViewSet,
    TaxRuleViewSet,
    TaxSummaryReportView,
)

router = DefaultRouter()
router.register(r"guests", GuestViewSet, basename="guest")
router.register(r"reservations", ReservationViewSet, basename="reservation")
router.register(r"folios", FolioViewSet, basename="folio")
router.register(r"invoices", InvoiceViewSet, basename="invoice")
router.register(r"payments", PaymentViewSet, basename="payment")
router.register(r"discounts", DiscountViewSet, basename="discount")
router.register(r"corporates", CorporateAccountViewSet, basename="corporate")
router.register(r"config/taxes", TaxRuleViewSet, basename="config-tax")
router.register(r"config/payment-methods", PaymentMethodViewSet, basename="config-payment-method")

urlpatterns = [
    path("", include(router.urls)),
    path("reports/daily", DailyReportView.as_view(), name="reports-daily"),
    path("reports/tax-summary", TaxSummaryReportView.as_view(), name="reports-tax"),
    path("reports/outstanding", OutstandingReportView.as_view(), name="reports-outstanding"),
    path("webhooks/pms", PMSWebhookView.as_view(), name="webhooks-pms"),
    path("webhooks/pos", POSWebhookView.as_view(), name="webhooks-pos"),
    path("webhooks/payment-gateway", PaymentGatewayWebhookView.as_view(), name="webhooks-payment"),
]
