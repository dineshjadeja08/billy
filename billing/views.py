from datetime import date
from decimal import Decimal
from io import BytesIO

from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from reportlab.pdfgen import canvas
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
	CorporateAccount,
	Discount,
	Folio,
	FolioItem,
	Invoice,
	InvoiceAdjustment,
	InvoiceLine,
	Payment,
	PaymentMethod,
	PaymentRefund,
	Reservation,
	TaxRule,
	WebhookEvent,
	Guest,
)
from .serializers import (
	CorporateAccountSerializer,
	DailyReportSerializer,
	DiscountSerializer,
	FolioItemSerializer,
	FolioSerializer,
	GuestSerializer,
	InvoiceAdjustmentSerializer,
	InvoiceSerializer,
	OutstandingInvoiceSerializer,
	PaymentMethodSerializer,
	PaymentRefundSerializer,
	PaymentSerializer,
	ReservationSerializer,
	TaxRuleSerializer,
	TaxSummarySerializer,
	WebhookEventSerializer,
)


class GuestViewSet(viewsets.ModelViewSet):
	queryset = Guest.objects.all().order_by("last_name", "first_name")
	serializer_class = GuestSerializer
	permission_classes = [permissions.IsAuthenticated]
	search_fields = ["first_name", "last_name", "email", "phone_number"]
	ordering_fields = ["first_name", "last_name", "created_at"]


class ReservationViewSet(viewsets.ModelViewSet):
	queryset = Reservation.objects.select_related("guest", "corporate_account").all()
	serializer_class = ReservationSerializer
	permission_classes = [permissions.IsAuthenticated]
	filterset_fields = ["status", "room_number", "corporate_account"]
	search_fields = ["reservation_number", "guest__first_name", "guest__last_name"]
	ordering_fields = ["check_in", "check_out", "reservation_number"]


class FolioViewSet(viewsets.ModelViewSet):
	queryset = Folio.objects.select_related("reservation", "corporate_account").prefetch_related(
		"items", "items__tax_rule", "folio_discounts", "folio_discounts__discount"
	)
	serializer_class = FolioSerializer
	permission_classes = [permissions.IsAuthenticated]
	filterset_fields = ["status", "currency", "corporate_account"]
	search_fields = ["folio_number", "guest_name"]
	ordering_fields = ["created_at", "folio_number"]

	def perform_create(self, serializer):
		reservation = serializer.validated_data.get("reservation")
		guest_name = serializer.validated_data.get("guest_name")
		if not guest_name and reservation:
			guest_name = str(reservation.guest)
		serializer.save(guest_name=guest_name or "Walk-in Guest")

	@action(detail=True, methods=["post"], url_path="items")
	def add_item(self, request, pk=None):
		folio = self.get_object()
		serializer = FolioItemSerializer(data=request.data, context={"request": request})
		serializer.is_valid(raise_exception=True)
		item = serializer.save(folio=folio, posted_by=request.user if request.user.is_authenticated else None)
		return Response(FolioItemSerializer(item).data, status=status.HTTP_201_CREATED)

	@extend_schema(
		parameters=[
			OpenApiParameter(
				name="item_id",
				type=OpenApiTypes.INT,
				location=OpenApiParameter.PATH,
				description="ID of the folio item to update",
			)
		]
	)
	@action(detail=True, methods=["put"], url_path="items/(?P<item_id>[^/.]+)")
	def update_item(self, request, pk=None, item_id=None):
		folio = self.get_object()
		item = get_object_or_404(folio.items, pk=item_id)
		serializer = FolioItemSerializer(item, data=request.data, context={"request": request})
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(FolioItemSerializer(item).data)

class InvoiceViewSet(viewsets.ModelViewSet):
	queryset = Invoice.objects.select_related("folio", "folio__reservation").prefetch_related(
		"lines", "invoice_discounts", "invoice_discounts__discount", "adjustments", "payments"
	)
	serializer_class = InvoiceSerializer
	permission_classes = [permissions.IsAuthenticated]
	filterset_fields = ["status", "currency", "folio__corporate_account"]
	search_fields = ["invoice_number", "folio__guest_name"]
	ordering_fields = ["issued_at", "invoice_number", "total"]

	@action(detail=True, methods=["get"], url_path="pdf")
	def pdf(self, request, pk=None):
		invoice = self.get_object()
		buffer = BytesIO()
		pdf = canvas.Canvas(buffer)
		pdf.setTitle(f"Invoice {invoice.invoice_number}")
		pdf.setFont("Helvetica-Bold", 16)
		pdf.drawString(40, 800, "Hotel Billing Invoice")
		pdf.setFont("Helvetica", 12)
		pdf.drawString(40, 770, f"Invoice #: {invoice.invoice_number}")
		pdf.drawString(40, 750, f"Issued: {invoice.issued_at:%Y-%m-%d}")
		pdf.drawString(40, 730, f"Guest: {invoice.folio.guest_name}")
		pdf.drawString(40, 710, f"Folio #: {invoice.folio.folio_number}")

		y = 670
		pdf.setFont("Helvetica-Bold", 12)
		pdf.drawString(40, y, "Description")
		pdf.drawString(300, y, "Qty")
		pdf.drawString(360, y, "Amount")
		y -= 20
		pdf.setFont("Helvetica", 11)
		for line in invoice.lines.all():
			pdf.drawString(40, y, line.description[:40])
			pdf.drawRightString(340, y, f"{line.quantity}")
			pdf.drawRightString(560, y, f"{line.net_amount + line.tax_amount:.2f}")
			y -= 16
			if y < 80:
				pdf.showPage()
				y = 780

		y -= 20
		pdf.setFont("Helvetica-Bold", 12)
		pdf.drawRightString(560, y, f"Subtotal: {invoice.subtotal:.2f}")
		y -= 16
		pdf.drawRightString(560, y, f"Tax: {invoice.tax_total:.2f}")
		y -= 16
		pdf.drawRightString(560, y, f"Discounts: {invoice.discount_total:.2f}")
		y -= 16
		pdf.drawRightString(560, y, f"Adjustments: {(invoice.total - (invoice.subtotal + invoice.tax_total - invoice.discount_total)):.2f}")
		y -= 16
		pdf.drawRightString(560, y, f"Total: {invoice.total:.2f}")
		y -= 16
		pdf.drawRightString(560, y, f"Balance Due: {invoice.balance_due:.2f}")

		pdf.showPage()
		pdf.save()
		buffer.seek(0)
		return FileResponse(
			buffer,
			as_attachment=True,
			filename=f"invoice-{invoice.invoice_number}.pdf",
			content_type="application/pdf",
		)

	@action(detail=True, methods=["post"], url_path="credit-note")
	def credit_note(self, request, pk=None):
		invoice = self.get_object()
		amount = Decimal(request.data.get("amount", "0"))
		reason = request.data.get("reason", "")
		if amount <= 0:
			return Response({"detail": "Amount must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)

		InvoiceAdjustment.objects.create(
			invoice=invoice,
			adjustment_type=InvoiceAdjustment.AdjustmentType.CREDIT,
			amount=-abs(amount),
			reason=reason,
		)
		invoice.recalculate_totals()
		return Response(InvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)

	@action(detail=True, methods=["post"], url_path="debit-note")
	def debit_note(self, request, pk=None):
		invoice = self.get_object()
		amount = Decimal(request.data.get("amount", "0"))
		reason = request.data.get("reason", "")
		if amount <= 0:
			return Response({"detail": "Amount must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)

		InvoiceAdjustment.objects.create(
			invoice=invoice,
			adjustment_type=InvoiceAdjustment.AdjustmentType.DEBIT,
			amount=abs(amount),
			reason=reason,
		)
		invoice.recalculate_totals()
		return Response(InvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)

	@action(detail=True, methods=["post"], url_path="payments")
	def create_payment(self, request, pk=None):
		invoice = self.get_object()
		serializer = PaymentSerializer(data=request.data, context={"request": request})
		serializer.is_valid(raise_exception=True)
		payment = serializer.save(invoice=invoice, processed_by=request.user)
		invoice.recalculate_totals()
		return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class PaymentViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
	queryset = Payment.objects.select_related("invoice", "payment_method")
	serializer_class = PaymentSerializer
	permission_classes = [permissions.IsAuthenticated]

	@action(detail=True, methods=["post"], url_path="refund")
	def refund(self, request, pk=None):
		payment = self.get_object()
		if payment.status != Payment.PaymentStatus.POSTED:
			return Response({"detail": "Only posted payments can be refunded."}, status=status.HTTP_400_BAD_REQUEST)

		amount = Decimal(request.data.get("amount", "0"))
		reason = request.data.get("reason", "")
		if amount <= 0 or amount > payment.amount:
			return Response({"detail": "Invalid refund amount."}, status=status.HTTP_400_BAD_REQUEST)

		refund = PaymentRefund.objects.create(
			payment=payment,
			amount=amount,
			reason=reason,
			processed_by=request.user,
		)
		payment.status = Payment.PaymentStatus.REFUNDED
		payment.save(update_fields=["status", "updated_at"])
		payment.invoice.recalculate_totals()
		return Response(PaymentRefundSerializer(refund).data, status=status.HTTP_201_CREATED)


class DiscountViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
	queryset = Discount.objects.all()
	serializer_class = DiscountSerializer
	permission_classes = [permissions.IsAdminUser]
	filterset_fields = ["is_active", "discount_type", "corporate_account"]
	search_fields = ["name"]
	ordering_fields = ["created_at", "name"]


class CorporateAccountViewSet(viewsets.ModelViewSet):
	queryset = CorporateAccount.objects.all()
	serializer_class = CorporateAccountSerializer
	permission_classes = [permissions.IsAuthenticated]
	search_fields = ["name", "code"]
	ordering_fields = ["name", "created_at"]

	@action(detail=True, methods=["get"], url_path="invoices")
	def invoices(self, request, pk=None):
		account = self.get_object()
		invoices = Invoice.objects.filter(folio__corporate_account=account)
		page = self.paginate_queryset(invoices)
		serializer = InvoiceSerializer(page or invoices, many=True)
		if page is not None:
			return self.get_paginated_response(serializer.data)
		return Response(serializer.data)


class TaxRuleViewSet(viewsets.ModelViewSet):
	queryset = TaxRule.objects.all()
	serializer_class = TaxRuleSerializer
	permission_classes = [permissions.IsAdminUser]
	filterset_fields = ["is_active"]
	ordering_fields = ["name", "created_at"]


class PaymentMethodViewSet(viewsets.ModelViewSet):
	queryset = PaymentMethod.objects.all()
	serializer_class = PaymentMethodSerializer
	permission_classes = [permissions.IsAdminUser]
	filterset_fields = ["is_active"]
	ordering_fields = ["name", "created_at"]


class DailyReportView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	@extend_schema(
		responses={200: DailyReportSerializer},
		parameters=[
			OpenApiParameter(
				name="date",
				type=OpenApiTypes.DATE,
				location=OpenApiParameter.QUERY,
				description="Target date for the report (YYYY-MM-DD). Defaults to today.",
				required=False,
			)
		],
		description="Generate a daily revenue report for a specific date."
	)
	def get(self, request):
		target_date = request.query_params.get("date")
		if target_date:
			target = date.fromisoformat(target_date)
		else:
			target = timezone.now().date()

		invoices = Invoice.objects.filter(issued_at__date=target)
		total_invoices = invoices.count()
		revenue = invoices.aggregate(total=Sum("total"))["total"] or Decimal("0.00")
		payments = (
			Payment.objects.filter(paid_at__date=target, status=Payment.PaymentStatus.POSTED)
			.aggregate(total=Sum("amount"))["total"]
			or Decimal("0.00")
		)

		payload = {
			"date": target,
			"total_invoices": total_invoices,
			"revenue": revenue,
			"payments": payments,
		}
		serializer = DailyReportSerializer(payload)
		return Response(serializer.data)


class TaxSummaryReportView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	@extend_schema(
		responses={200: TaxSummarySerializer(many=True)},
		parameters=[
			OpenApiParameter(
				name="start_date",
				type=OpenApiTypes.DATE,
				location=OpenApiParameter.QUERY,
				description="Start date for the tax summary (YYYY-MM-DD). Defaults to today.",
				required=False,
			),
			OpenApiParameter(
				name="end_date",
				type=OpenApiTypes.DATE,
				location=OpenApiParameter.QUERY,
				description="End date for the tax summary (YYYY-MM-DD). Defaults to start_date.",
				required=False,
			)
		],
		description="Generate a tax summary report grouped by tax rule for a date range."
	)
	def get(self, request):
		start_date = request.query_params.get("start_date")
		end_date = request.query_params.get("end_date")
		if start_date:
			start = date.fromisoformat(start_date)
		else:
			start = timezone.now().date()
		if end_date:
			end = date.fromisoformat(end_date)
		else:
			end = start

		lines = (
			InvoiceLine.objects.filter(invoice__issued_at__date__range=(start, end))
			.select_related("folio_item__tax_rule")
			.exclude(folio_item__tax_rule__isnull=True)
		)
		summaries = (
			lines.values("folio_item__tax_rule__name")
			.annotate(
				taxable_amount=Sum("net_amount"),
				tax_amount=Sum("tax_amount"),
			)
			.order_by("folio_item__tax_rule__name")
		)
		data = [
			{
				"tax_rule": entry["folio_item__tax_rule__name"],
				"taxable_amount": entry["taxable_amount"] or Decimal("0.00"),
				"tax_amount": entry["tax_amount"] or Decimal("0.00"),
			}
			for entry in summaries
		]
		serializer = TaxSummarySerializer(data, many=True)
		return Response(serializer.data)


class OutstandingReportView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	@extend_schema(
		responses={200: OutstandingInvoiceSerializer(many=True)},
		description="List all invoices with outstanding balances (balance_due > 0)."
	)
	def get(self, request):
		invoices = Invoice.objects.filter(status__in=[Invoice.InvoiceStatus.ISSUED, Invoice.InvoiceStatus.PAID])
		outstanding = []
		for invoice in invoices:
			balance = invoice.balance_due
			if balance > 0:
				outstanding.append(
					{
						"invoice_id": invoice.pk,
						"invoice_number": invoice.invoice_number,
						"guest_name": invoice.folio.guest_name,
						"balance_due": balance,
						"issued_at": invoice.issued_at,
					}
				)
		serializer = OutstandingInvoiceSerializer(outstanding, many=True)
		return Response(serializer.data)


class BaseWebhookView(APIView):
	permission_classes = [permissions.AllowAny]
	authentication_classes = []
	source = None

	@extend_schema(
		request=WebhookEventSerializer,
		responses={202: WebhookEventSerializer},
		description="Receive webhook events from external systems."
	)
	def post(self, request):
		event = WebhookEvent.objects.create(
			source=self.source,
			event_type=request.data.get("event_type", ""),
			payload=request.data,
			status="received",
		)
		serializer = WebhookEventSerializer(event)
		return Response(serializer.data, status=status.HTTP_202_ACCEPTED)


class PMSWebhookView(BaseWebhookView):
	source = WebhookEvent.WebhookSource.PMS


class POSWebhookView(BaseWebhookView):
	source = WebhookEvent.WebhookSource.POS


class PaymentGatewayWebhookView(BaseWebhookView):
	source = WebhookEvent.WebhookSource.PAYMENT_GATEWAY


# PayPal Payment Views
class PayPalCreatePaymentView(APIView):
	"""Create a PayPal payment for an invoice"""
	permission_classes = [permissions.IsAuthenticated]

	@extend_schema(
		request={
			"application/json": {
				"type": "object",
				"properties": {
					"invoice_id": {"type": "integer", "description": "Invoice ID to create payment for"}
				},
				"required": ["invoice_id"]
			}
		},
		responses={
			200: {
				"type": "object",
				"properties": {
					"success": {"type": "boolean"},
					"payment_id": {"type": "string"},
					"approval_url": {"type": "string"},
					"status": {"type": "string"}
				}
			}
		},
		description="Create a PayPal payment for an invoice. Returns approval URL to redirect user."
	)
	def post(self, request):
		from .paypal_service import PayPalService
		
		invoice_id = request.data.get("invoice_id")
		if not invoice_id:
			return Response(
				{"error": "invoice_id is required"},
				status=status.HTTP_400_BAD_REQUEST
			)
		
		try:
			invoice = Invoice.objects.get(pk=invoice_id)
		except Invoice.DoesNotExist:
			return Response(
				{"error": "Invoice not found"},
				status=status.HTTP_404_NOT_FOUND
			)
		
		# Check if invoice has balance due
		if invoice.balance_due <= 0:
			return Response(
				{"error": "Invoice is already paid"},
				status=status.HTTP_400_BAD_REQUEST
			)
		
		# Create PayPal payment
		paypal_service = PayPalService()
		result = paypal_service.create_payment(invoice)
		
		if result["success"]:
			return Response(result, status=status.HTTP_200_OK)
		else:
			return Response(
				{"error": "Failed to create PayPal payment", "details": result.get("error")},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)


class PayPalExecutePaymentView(APIView):
	"""Execute a PayPal payment after user approval"""
	permission_classes = [permissions.AllowAny]  # PayPal redirects here
	
	@extend_schema(
		parameters=[
			OpenApiParameter(
				name="paymentId",
				type=OpenApiTypes.STR,
				location=OpenApiParameter.QUERY,
				description="PayPal payment ID",
				required=True
			),
			OpenApiParameter(
				name="PayerID",
				type=OpenApiTypes.STR,
				location=OpenApiParameter.QUERY,
				description="PayPal payer ID",
				required=True
			)
		],
		responses={
			200: {
				"type": "object",
				"properties": {
					"success": {"type": "boolean"},
					"message": {"type": "string"},
					"payment_id": {"type": "integer"},
					"invoice_id": {"type": "integer"}
				}
			}
		},
		description="Execute PayPal payment after user approval (called by PayPal redirect)"
	)
	def get(self, request):
		from .paypal_service import PayPalService
		from .serializers import PaymentSerializer
		
		payment_id = request.query_params.get("paymentId")
		payer_id = request.query_params.get("PayerID")
		
		if not payment_id or not payer_id:
			return Response(
				{"error": "paymentId and PayerID are required"},
				status=status.HTTP_400_BAD_REQUEST
			)
		
		# Execute payment
		paypal_service = PayPalService()
		result = paypal_service.execute_payment(payment_id, payer_id)
		
		if not result["success"]:
			return Response(
				{"error": "Failed to execute payment", "details": result.get("error")},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)
		
		# Get invoice
		invoice_id = result.get("invoice_id")
		if not invoice_id:
			return Response(
				{"error": "Invoice ID not found in payment"},
				status=status.HTTP_400_BAD_REQUEST
			)
		
		try:
			invoice = Invoice.objects.get(pk=invoice_id)
		except Invoice.DoesNotExist:
			return Response(
				{"error": "Invoice not found"},
				status=status.HTTP_404_NOT_FOUND
			)
		
		# Get or create PayPal payment method
		payment_method, _ = PaymentMethod.objects.get_or_create(
			name="PayPal",
			defaults={"is_active": True}
		)
		
		# Create payment record
		payment = Payment.objects.create(
			invoice=invoice,
			payment_method=payment_method,
			amount=result["amount"],
			reference=result.get("transaction_id", payment_id),
			status=Payment.PaymentStatus.POSTED,
			notes=f"PayPal payment ID: {payment_id}, Payer email: {result.get('payer_email', 'N/A')}"
		)
		
		# Update invoice status
		invoice.recalculate_totals()
		if invoice.balance_due <= 0:
			invoice.status = Invoice.InvoiceStatus.PAID
			invoice.save(update_fields=["status", "updated_at"])
		
		return Response({
			"success": True,
			"message": "Payment completed successfully",
			"payment_id": payment.id,
			"invoice_id": invoice.id,
			"invoice_number": invoice.invoice_number,
			"amount_paid": str(payment.amount),
			"balance_due": str(invoice.balance_due)
		}, status=status.HTTP_200_OK)


class PayPalCancelPaymentView(APIView):
	"""Handle PayPal payment cancellation"""
	permission_classes = [permissions.AllowAny]
	
	@extend_schema(
		description="Handle PayPal payment cancellation (called by PayPal redirect)"
	)
	def get(self, request):
		return Response({
			"message": "Payment cancelled by user"
		}, status=status.HTTP_200_OK)


class PayPalRefundView(APIView):
	"""Refund a PayPal payment"""
	permission_classes = [permissions.IsAuthenticated]
	
	@extend_schema(
		request={
			"application/json": {
				"type": "object",
				"properties": {
					"payment_id": {"type": "integer", "description": "Payment ID to refund"},
					"amount": {"type": "number", "description": "Amount to refund (optional, full refund if not provided)"},
					"reason": {"type": "string", "description": "Refund reason"}
				},
				"required": ["payment_id"]
			}
		},
		responses={200: {"type": "object"}},
		description="Refund a PayPal payment (full or partial)"
	)
	def post(self, request):
		from .paypal_service import PayPalService
		
		payment_id = request.data.get("payment_id")
		amount = request.data.get("amount")
		reason = request.data.get("reason", "")
		
		if not payment_id:
			return Response(
				{"error": "payment_id is required"},
				status=status.HTTP_400_BAD_REQUEST
			)
		
		try:
			payment = Payment.objects.get(pk=payment_id)
		except Payment.DoesNotExist:
			return Response(
				{"error": "Payment not found"},
				status=status.HTTP_404_NOT_FOUND
			)
		
		# Check if payment is via PayPal
		if payment.payment_method.name != "PayPal":
			return Response(
				{"error": "Payment is not via PayPal"},
				status=status.HTTP_400_BAD_REQUEST
			)
		
		# Check if already refunded
		if payment.status == Payment.PaymentStatus.REFUNDED:
			return Response(
				{"error": "Payment is already refunded"},
				status=status.HTTP_400_BAD_REQUEST
			)
		
		# Extract PayPal transaction ID from reference
		transaction_id = payment.reference
		
		# Process refund
		paypal_service = PayPalService()
		if amount:
			amount = Decimal(amount)
			result = paypal_service.refund_payment(transaction_id, amount)
		else:
			amount = payment.amount
			result = paypal_service.refund_payment(transaction_id)
		
		if not result["success"]:
			return Response(
				{"error": "Failed to process refund", "details": result.get("error")},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)
		
		# Create refund record
		refund = PaymentRefund.objects.create(
			payment=payment,
			amount=amount,
			reason=reason,
			processed_by=request.user,
			notes=f"PayPal refund ID: {result.get('refund_id', 'N/A')}"
		)
		
		# Update payment status
		payment.status = Payment.PaymentStatus.REFUNDED
		payment.save(update_fields=["status", "updated_at"])
		
		# Recalculate invoice
		payment.invoice.recalculate_totals()
		
		return Response({
			"success": True,
			"message": "Refund processed successfully",
			"refund_id": refund.id,
			"amount": str(refund.amount),
			"paypal_refund_id": result.get("refund_id")
		}, status=status.HTTP_200_OK)
