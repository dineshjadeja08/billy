from datetime import date
from decimal import Decimal
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True


class Guest(TimeStampedModel):
	first_name = models.CharField(max_length=120)
	last_name = models.CharField(max_length=120)
	email = models.EmailField(blank=True)
	phone_number = models.CharField(max_length=50, blank=True)
	company_name = models.CharField(max_length=120, blank=True)

	class Meta:
		ordering = ["last_name", "first_name"]

	def __str__(self) -> str:  # pragma: no cover - human readable string
		return f"{self.first_name} {self.last_name}".strip()


class CorporateAccount(TimeStampedModel):
	name = models.CharField(max_length=200)
	code = models.CharField(max_length=40, unique=True)
	contact_email = models.EmailField(blank=True)
	contact_phone = models.CharField(max_length=50, blank=True)
	discount_rate = models.DecimalField(
		max_digits=5, decimal_places=2, default=Decimal("0.00")
	)
	notes = models.TextField(blank=True)

	class Meta:
		ordering = ["name"]

	def __str__(self) -> str:  # pragma: no cover
		return self.name


class Discount(TimeStampedModel):
	class DiscountType(models.TextChoices):
		PERCENTAGE = "percentage", "Percentage"
		FIXED = "fixed", "Fixed Amount"

	name = models.CharField(max_length=160)
	discount_type = models.CharField(
		max_length=20, choices=DiscountType.choices, default=DiscountType.PERCENTAGE
	)
	value = models.DecimalField(max_digits=10, decimal_places=2)
	is_active = models.BooleanField(default=True)
	start_date = models.DateField(null=True, blank=True)
	end_date = models.DateField(null=True, blank=True)
	corporate_account = models.ForeignKey(
		CorporateAccount, related_name="discounts", on_delete=models.CASCADE, null=True, blank=True
	)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self) -> str:  # pragma: no cover
		return self.name

	def is_applicable(self, target_date: date | None = None) -> bool:
		today = target_date or timezone.now().date()
		if not self.is_active:
			return False
		if self.start_date and today < self.start_date:
			return False
		if self.end_date and today > self.end_date:
			return False
		return True


class TaxRule(TimeStampedModel):
	name = models.CharField(max_length=120)
	rate = models.DecimalField(max_digits=5, decimal_places=2)
	is_active = models.BooleanField(default=True)
	description = models.TextField(blank=True)

	class Meta:
		ordering = ["name"]

	def __str__(self) -> str:  # pragma: no cover
		return f"{self.name} ({self.rate}%)"


class PaymentMethod(TimeStampedModel):
	name = models.CharField(max_length=120, unique=True)
	is_active = models.BooleanField(default=True)
	requires_reference = models.BooleanField(default=False)

	class Meta:
		ordering = ["name"]

	def __str__(self) -> str:  # pragma: no cover
		return self.name


class Reservation(TimeStampedModel):
	class ReservationStatus(models.TextChoices):
		BOOKED = "booked", "Booked"
		CHECKED_IN = "checked_in", "Checked In"
		CHECKED_OUT = "checked_out", "Checked Out"
		CANCELLED = "cancelled", "Cancelled"

	guest = models.ForeignKey(Guest, related_name="reservations", on_delete=models.CASCADE)
	corporate_account = models.ForeignKey(
		CorporateAccount,
		related_name="reservations",
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
	)
	reservation_number = models.CharField(max_length=40, unique=True)
	status = models.CharField(
		max_length=20, choices=ReservationStatus.choices, default=ReservationStatus.BOOKED
	)
	check_in = models.DateField()
	check_out = models.DateField()
	room_number = models.CharField(max_length=20)
	rate_plan = models.CharField(max_length=120, blank=True)
	number_of_guests = models.PositiveIntegerField(default=1)
	notes = models.TextField(blank=True)

	class Meta:
		ordering = ["-check_in", "reservation_number"]

	def __str__(self) -> str:  # pragma: no cover
		return f"Reservation {self.reservation_number}"


def _folio_number() -> str:
	return uuid.uuid4().hex[:10].upper()


class Folio(TimeStampedModel):
	class FolioStatus(models.TextChoices):
		OPEN = "open", "Open"
		CLOSED = "closed", "Closed"
		SETTLED = "settled", "Settled"

	reservation = models.ForeignKey(
		Reservation,
		related_name="folios",
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
	)
	guest_name = models.CharField(max_length=240)
	corporate_account = models.ForeignKey(
		CorporateAccount,
		related_name="folios",
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
	)
	folio_number = models.CharField(max_length=20, unique=True, default=_folio_number)
	currency = models.CharField(max_length=3, default="USD")
	status = models.CharField(
		max_length=20, choices=FolioStatus.choices, default=FolioStatus.OPEN
	)
	notes = models.TextField(blank=True)

	discounts = models.ManyToManyField(Discount, through="FolioDiscount", blank=True)

	class Meta:
		ordering = ["-created_at", "folio_number"]

	def __str__(self) -> str:  # pragma: no cover
		return f"Folio {self.folio_number}"

	@property
	def subtotal(self) -> Decimal:
		return sum((item.line_total for item in self.items.all()), Decimal("0.00"))

	@property
	def tax_total(self) -> Decimal:
		return sum((item.tax_amount for item in self.items.all()), Decimal("0.00"))

	@property
	def total(self) -> Decimal:
		return self.subtotal + self.tax_total


class FolioDiscount(TimeStampedModel):
	folio = models.ForeignKey(Folio, related_name="folio_discounts", on_delete=models.CASCADE)
	discount = models.ForeignKey(Discount, related_name="folio_discounts", on_delete=models.CASCADE)
	applied_value = models.DecimalField(max_digits=10, decimal_places=2)

	class Meta:
		unique_together = ("folio", "discount")


class FolioItem(TimeStampedModel):
	class ItemType(models.TextChoices):
		ROOM = "room", "Room Charge"
		SERVICE = "service", "Service Charge"
		ADJUSTMENT = "adjustment", "Adjustment"

	folio = models.ForeignKey(Folio, related_name="items", on_delete=models.CASCADE)
	description = models.CharField(max_length=240)
	item_type = models.CharField(max_length=20, choices=ItemType.choices)
	quantity = models.DecimalField(max_digits=9, decimal_places=2, default=Decimal("1.00"))
	unit_price = models.DecimalField(max_digits=10, decimal_places=2)
	tax_rule = models.ForeignKey(
		TaxRule,
		related_name="folio_items",
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
	)
	posted_at = models.DateTimeField(default=timezone.now)
	posted_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		related_name="posted_folio_items",
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
	)

	class Meta:
		ordering = ["-posted_at"]

	@property
	def line_total(self) -> Decimal:
		return self.quantity * self.unit_price

	@property
	def tax_amount(self) -> Decimal:
		if not self.tax_rule or not self.tax_rule.is_active:
			return Decimal("0.00")
		return (self.line_total * self.tax_rule.rate) / Decimal("100.00")


def _invoice_number() -> str:
	return uuid.uuid4().hex[:12].upper()


class Invoice(TimeStampedModel):
	class InvoiceStatus(models.TextChoices):
		DRAFT = "draft", "Draft"
		ISSUED = "issued", "Issued"
		PAID = "paid", "Paid"
		VOID = "void", "Void"

	folio = models.ForeignKey(Folio, related_name="invoices", on_delete=models.CASCADE)
	invoice_number = models.CharField(max_length=25, unique=True, default=_invoice_number)
	status = models.CharField(
		max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.ISSUED
	)
	issued_at = models.DateTimeField(default=timezone.now)
	due_date = models.DateField(null=True, blank=True)
	currency = models.CharField(max_length=3, default="USD")
	subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
	discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
	tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
	total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
	notes = models.TextField(blank=True)

	discounts = models.ManyToManyField(Discount, through="InvoiceDiscount", blank=True)

	class Meta:
		ordering = ["-issued_at", "invoice_number"]

	def __str__(self) -> str:  # pragma: no cover
		return f"Invoice {self.invoice_number}"

	def recalculate_totals(self) -> None:
		line_totals = self.lines.aggregate(
			subtotal=models.Sum("net_amount"), tax=models.Sum("tax_amount")
		)
		subtotal = line_totals.get("subtotal") or Decimal("0.00")
		tax_total = line_totals.get("tax") or Decimal("0.00")
		discount_total = (
			self.invoice_discounts.aggregate(total=models.Sum("applied_amount"))["total"]
			or Decimal("0.00")
		)
		adjustment_total = (
			self.adjustments.aggregate(total=models.Sum("amount"))["total"]
			or Decimal("0.00")
		)
		self.subtotal = subtotal
		self.tax_total = tax_total
		self.discount_total = discount_total
		self.total = subtotal + tax_total - discount_total + adjustment_total
		self.save(update_fields=["subtotal", "tax_total", "discount_total", "total", "updated_at"])

	@property
	def balance_due(self) -> Decimal:
		payments = self.payments.filter(status=Payment.PaymentStatus.POSTED).aggregate(
			total=models.Sum("amount")
		)
		paid = payments.get("total") or Decimal("0.00")
		return self.total - paid


class InvoiceLine(TimeStampedModel):
	invoice = models.ForeignKey(Invoice, related_name="lines", on_delete=models.CASCADE)
	folio_item = models.ForeignKey(
		FolioItem, related_name="invoice_lines", on_delete=models.SET_NULL, null=True, blank=True
	)
	description = models.CharField(max_length=240)
	quantity = models.DecimalField(max_digits=9, decimal_places=2, default=Decimal("1.00"))
	unit_price = models.DecimalField(max_digits=10, decimal_places=2)
	net_amount = models.DecimalField(max_digits=12, decimal_places=2)
	tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))


class InvoiceDiscount(TimeStampedModel):
	invoice = models.ForeignKey(Invoice, related_name="invoice_discounts", on_delete=models.CASCADE)
	discount = models.ForeignKey(Discount, related_name="invoice_discounts", on_delete=models.CASCADE)
	applied_amount = models.DecimalField(max_digits=12, decimal_places=2)

	class Meta:
		unique_together = ("invoice", "discount")


class InvoiceAdjustment(TimeStampedModel):
	class AdjustmentType(models.TextChoices):
		CREDIT = "credit", "Credit Note"
		DEBIT = "debit", "Debit Note"

	invoice = models.ForeignKey(Invoice, related_name="adjustments", on_delete=models.CASCADE)
	adjustment_type = models.CharField(max_length=12, choices=AdjustmentType.choices)
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	reason = models.CharField(max_length=255, blank=True)


class Payment(TimeStampedModel):
	class PaymentStatus(models.TextChoices):
		POSTED = "posted", "Posted"
		REFUNDED = "refunded", "Refunded"
		VOID = "void", "Void"

	invoice = models.ForeignKey(Invoice, related_name="payments", on_delete=models.CASCADE)
	payment_method = models.ForeignKey(
		PaymentMethod,
		related_name="payments",
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
	)
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	paid_at = models.DateTimeField(default=timezone.now)
	reference = models.CharField(max_length=120, blank=True)
	status = models.CharField(
		max_length=12, choices=PaymentStatus.choices, default=PaymentStatus.POSTED
	)
	processed_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		related_name="processed_payments",
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
	)
	notes = models.TextField(blank=True)


class PaymentRefund(TimeStampedModel):
	payment = models.ForeignKey(Payment, related_name="refunds", on_delete=models.CASCADE)
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	reason = models.CharField(max_length=255, blank=True)
	processed_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		related_name="processed_refunds",
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
	)


class WebhookEvent(TimeStampedModel):
	class WebhookSource(models.TextChoices):
		PMS = "pms", "Property Management System"
		POS = "pos", "Point of Sale"
		PAYMENT_GATEWAY = "payment_gateway", "Payment Gateway"

	source = models.CharField(max_length=32, choices=WebhookSource.choices)
	event_type = models.CharField(max_length=120, blank=True)
	payload = models.JSONField()
	status = models.CharField(max_length=40, default="received")
	processed_at = models.DateTimeField(null=True, blank=True)
	notes = models.TextField(blank=True)

	class Meta:
		ordering = ["-created_at"]
