from django.contrib import admin

from .models import (
	CorporateAccount,
	Discount,
	Folio,
	FolioItem,
	Guest,
	Invoice,
	InvoiceAdjustment,
	InvoiceDiscount,
	InvoiceLine,
	Payment,
	PaymentMethod,
	Reservation,
	TaxRule,
	WebhookEvent,
)


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
	list_display = ("first_name", "last_name", "email", "phone_number")
	search_fields = ("first_name", "last_name", "email")


@admin.register(CorporateAccount)
class CorporateAccountAdmin(admin.ModelAdmin):
	list_display = ("name", "code", "discount_rate")
	search_fields = ("name", "code")


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
	list_display = ("reservation_number", "guest", "check_in", "check_out", "status")
	list_filter = ("status",)
	search_fields = ("reservation_number", "guest__first_name", "guest__last_name")


class FolioItemInline(admin.TabularInline):
	model = FolioItem
	extra = 0


@admin.register(Folio)
class FolioAdmin(admin.ModelAdmin):
	list_display = ("folio_number", "guest_name", "status", "created_at")
	list_filter = ("status",)
	search_fields = ("folio_number", "guest_name")
	inlines = [FolioItemInline]


class InvoiceLineInline(admin.TabularInline):
	model = InvoiceLine
	extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
	list_display = ("invoice_number", "folio", "status", "total", "issued_at")
	list_filter = ("status",)
	search_fields = ("invoice_number", "folio__folio_number")
	inlines = [InvoiceLineInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
	list_display = ("invoice", "amount", "paid_at", "status")
	list_filter = ("status",)
	search_fields = ("invoice__invoice_number", "reference")


admin.site.register(Discount)
admin.site.register(TaxRule)
admin.site.register(PaymentMethod)
admin.site.register(InvoiceDiscount)
admin.site.register(InvoiceAdjustment)
admin.site.register(WebhookEvent)
