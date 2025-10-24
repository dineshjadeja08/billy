from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    CorporateAccount,
    Discount,
    Folio,
    FolioDiscount,
    FolioItem,
    Guest,
    Invoice,
    InvoiceAdjustment,
    InvoiceDiscount,
    InvoiceLine,
    Payment,
    PaymentMethod,
    PaymentRefund,
    Reservation,
    TaxRule,
    WebhookEvent,
)


User = get_user_model()


class GuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guest
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "company_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CorporateAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CorporateAccount
        fields = [
            "id",
            "name",
            "code",
            "contact_email",
            "contact_phone",
            "discount_rate",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = [
            "id",
            "name",
            "discount_type",
            "value",
            "is_active",
            "start_date",
            "end_date",
            "corporate_account",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TaxRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxRule
        fields = ["id", "name", "rate", "is_active", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ["id", "name", "is_active", "requires_reference", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ReservationSerializer(serializers.ModelSerializer):
    guest = GuestSerializer(read_only=True)
    guest_id = serializers.PrimaryKeyRelatedField(
        source="guest", queryset=Guest.objects.all(), write_only=True
    )
    corporate_account = CorporateAccountSerializer(read_only=True)
    corporate_account_id = serializers.PrimaryKeyRelatedField(
        source="corporate_account",
        queryset=CorporateAccount.objects.all(),
        allow_null=True,
        required=False,
        write_only=True,
    )

    class Meta:
        model = Reservation
        fields = [
            "id",
            "reservation_number",
            "status",
            "check_in",
            "check_out",
            "room_number",
            "rate_plan",
            "number_of_guests",
            "notes",
            "guest",
            "guest_id",
            "corporate_account",
            "corporate_account_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "guest", "corporate_account"]


class FolioItemSerializer(serializers.ModelSerializer):
    tax_rule = TaxRuleSerializer(read_only=True)
    tax_rule_id = serializers.PrimaryKeyRelatedField(
        source="tax_rule",
        queryset=TaxRule.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    tax_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = FolioItem
        fields = [
            "id",
            "description",
            "item_type",
            "quantity",
            "unit_price",
            "tax_rule",
            "tax_rule_id",
            "posted_at",
            "posted_by",
            "line_total",
            "tax_amount",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "tax_rule",
            "posted_by",
            "line_total",
            "tax_amount",
            "created_at",
            "updated_at",
        ]


class FolioDiscountSerializer(serializers.ModelSerializer):
    discount = DiscountSerializer(read_only=True)
    discount_id = serializers.PrimaryKeyRelatedField(
        source="discount", queryset=Discount.objects.all(), write_only=True
    )

    class Meta:
        model = FolioDiscount
        fields = [
            "id",
            "discount",
            "discount_id",
            "applied_value",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "discount", "created_at", "updated_at"]


class FolioSerializer(serializers.ModelSerializer):
    reservation = ReservationSerializer(read_only=True)
    reservation_id = serializers.PrimaryKeyRelatedField(
        source="reservation",
        queryset=Reservation.objects.all(),
        allow_null=True,
        required=False,
        write_only=True,
    )
    corporate_account = CorporateAccountSerializer(read_only=True)
    corporate_account_id = serializers.PrimaryKeyRelatedField(
        source="corporate_account",
        queryset=CorporateAccount.objects.all(),
        allow_null=True,
        required=False,
        write_only=True,
    )
    items = FolioItemSerializer(many=True, read_only=True)
    discounts = FolioDiscountSerializer(many=True, source="folio_discounts", read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    tax_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Folio
        fields = [
            "id",
            "folio_number",
            "guest_name",
            "corporate_account",
            "reservation",
            "reservation_id",
            "corporate_account_id",
            "currency",
            "status",
            "notes",
            "items",
            "discounts",
            "subtotal",
            "tax_total",
            "total",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "folio_number",
            "reservation",
            "corporate_account",
            "items",
            "discounts",
            "subtotal",
            "tax_total",
            "total",
            "created_at",
            "updated_at",
        ]


class InvoiceLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLine
        fields = [
            "id",
            "description",
            "quantity",
            "unit_price",
            "net_amount",
            "tax_amount",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class InvoiceDiscountSerializer(serializers.ModelSerializer):
    discount = DiscountSerializer(read_only=True)

    class Meta:
        model = InvoiceDiscount
        fields = ["id", "discount", "applied_amount", "created_at", "updated_at"]
        read_only_fields = fields


class InvoiceAdjustmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceAdjustment
        fields = [
            "id",
            "adjustment_type",
            "amount",
            "reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PaymentSerializer(serializers.ModelSerializer):
    payment_method = PaymentMethodSerializer(read_only=True)
    payment_method_id = serializers.PrimaryKeyRelatedField(
        source="payment_method",
        queryset=PaymentMethod.objects.all(),
        allow_null=True,
        required=False,
        write_only=True,
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "invoice",
            "payment_method",
            "payment_method_id",
            "amount",
            "paid_at",
            "reference",
            "status",
            "processed_by",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "invoice",
            "payment_method",
            "processed_by",
            "created_at",
            "updated_at",
        ]


class PaymentRefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentRefund
        fields = ["id", "payment", "amount", "reason", "processed_by", "created_at", "updated_at"]
        read_only_fields = ["id", "payment", "processed_by", "created_at", "updated_at"]


class InvoiceSerializer(serializers.ModelSerializer):
    folio = FolioSerializer(read_only=True)
    folio_id = serializers.PrimaryKeyRelatedField(
        source="folio", queryset=Folio.objects.all(), write_only=True
    )
    lines = InvoiceLineSerializer(many=True, read_only=True)
    invoice_discounts = InvoiceDiscountSerializer(many=True, read_only=True)
    adjustments = InvoiceAdjustmentSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    balance_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    discount_ids = serializers.PrimaryKeyRelatedField(
        queryset=Discount.objects.filter(is_active=True),
        many=True,
        write_only=True,
        required=False,
    )

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "status",
            "issued_at",
            "due_date",
            "currency",
            "subtotal",
            "discount_total",
            "tax_total",
            "total",
            "notes",
            "folio",
            "folio_id",
            "lines",
            "invoice_discounts",
            "adjustments",
            "payments",
            "balance_due",
            "discount_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "invoice_number",
            "subtotal",
            "discount_total",
            "tax_total",
            "total",
            "folio",
            "lines",
            "invoice_discounts",
            "adjustments",
            "payments",
            "balance_due",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        discount_ids = validated_data.pop("discount_ids", [])
        invoice = super().create(validated_data)
        folio = invoice.folio
        subtotal = Decimal("0.00")
        tax_total = Decimal("0.00")

        for item in folio.items.all():
            line_total = item.line_total
            tax_amount = item.tax_amount
            InvoiceLine.objects.create(
                invoice=invoice,
                folio_item=item,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                net_amount=line_total,
                tax_amount=tax_amount,
            )
            subtotal += line_total
            tax_total += tax_amount

        if discount_ids:
            discounts = Discount.objects.filter(id__in=[d.id for d in discount_ids], is_active=True)
            base_amount = subtotal + tax_total
            for discount in discounts:
                applied = self._calculate_discount(base_amount, discount)
                InvoiceDiscount.objects.create(
                    invoice=invoice,
                    discount=discount,
                    applied_amount=applied,
                )

        invoice.recalculate_totals()
        return invoice

    def _calculate_discount(self, base_amount: Decimal, discount: Discount) -> Decimal:
        if discount.discount_type == Discount.DiscountType.PERCENTAGE:
            return (base_amount * discount.value) / Decimal("100.00")
        return discount.value


class WebhookEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookEvent
        fields = [
            "id",
            "source",
            "event_type",
            "payload",
            "status",
            "processed_at",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "processed_at", "created_at", "updated_at"]


class DailyReportSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_invoices = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    payments = serializers.DecimalField(max_digits=12, decimal_places=2)


class TaxSummarySerializer(serializers.Serializer):
    tax_rule = serializers.CharField()
    taxable_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class OutstandingInvoiceSerializer(serializers.Serializer):
    invoice_id = serializers.IntegerField()
    invoice_number = serializers.CharField()
    guest_name = serializers.CharField()
    balance_due = serializers.DecimalField(max_digits=12, decimal_places=2)
    issued_at = serializers.DateTimeField()
