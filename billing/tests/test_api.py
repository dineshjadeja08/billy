from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase, APIClient


class BillingApiTests(APITestCase):
    client: APIClient  # type: ignore[assignment]

    def setUp(self) -> None:
        User = get_user_model()
        self.admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="Str0ngPass!",
        )
        self.client.force_authenticate(user=self.admin)  # type: ignore[attr-defined]

    def test_end_to_end_invoice_flow(self) -> None:
        guest_response = self.client.post(  # type: ignore[misc]
            reverse("guest-list"),
            {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "phone_number": "1234567890",
                "company_name": "Test Corp",
            },
            format="json",
        )
        self.assertEqual(guest_response.status_code, status.HTTP_201_CREATED)  # type: ignore[attr-defined]
        guest_id = guest_response.data["id"]  # type: ignore[index]

        today = timezone.now().date()
        reservation_response = self.client.post(  # type: ignore[misc]
            reverse("reservation-list"),
            {
                "guest_id": guest_id,
                "reservation_number": "RES-1001",
                "status": "booked",
                "check_in": today.isoformat(),
                "check_out": (today + timedelta(days=2)).isoformat(),
                "room_number": "101",
                "rate_plan": "BAR",
                "number_of_guests": 2,
                "notes": "VIP",
            },
            format="json",
        )
        self.assertEqual(reservation_response.status_code, status.HTTP_201_CREATED)  # type: ignore[attr-defined]
        reservation_id = reservation_response.data["id"]  # type: ignore[index]

        folio_response = self.client.post(  # type: ignore[misc]
            reverse("folio-list"),
            {
                "guest_name": "John Doe",
                "reservation_id": reservation_id,
                "currency": "USD",
                "status": "open",
                "notes": "Room folio",
            },
            format="json",
        )
        self.assertEqual(folio_response.status_code, status.HTTP_201_CREATED)  # type: ignore[attr-defined]
        folio_id = folio_response.data["id"]  # type: ignore[index]

        item_response = self.client.post(  # type: ignore[misc]
            reverse("folio-add-item", kwargs={"pk": folio_id}),
            {
                "description": "Room Night",
                "item_type": "room",
                "quantity": "2",
                "unit_price": "150.00",
            },
            format="json",
        )
        self.assertEqual(item_response.status_code, status.HTTP_201_CREATED)  # type: ignore[attr-defined]

        discount_response = self.client.post(  # type: ignore[misc]
            reverse("discount-list"),
            {
                "name": "VIP Discount",
                "discount_type": "percentage",
                "value": "10.00",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(discount_response.status_code, status.HTTP_201_CREATED)  # type: ignore[attr-defined]
        discount_id = discount_response.data["id"]  # type: ignore[index]

        payment_method_response = self.client.post(  # type: ignore[misc]
            reverse("config-payment-method-list"),
            {"name": "Cash", "is_active": True, "requires_reference": False},
            format="json",
        )
        self.assertEqual(payment_method_response.status_code, status.HTTP_201_CREATED)  # type: ignore[attr-defined]
        payment_method_id = payment_method_response.data["id"]  # type: ignore[index]

        invoice_response = self.client.post(  # type: ignore[misc]
            reverse("invoice-list"),
            {
                "folio_id": folio_id,
                "discount_ids": [discount_id],
                "notes": "Checkout invoice",
            },
            format="json",
        )
        self.assertEqual(invoice_response.status_code, status.HTTP_201_CREATED)  # type: ignore[attr-defined]
        invoice_id = invoice_response.data["id"]  # type: ignore[index]
        invoice_total = Decimal(invoice_response.data["total"])  # type: ignore[index]

        payment_response = self.client.post(  # type: ignore[misc]
            reverse("invoice-create-payment", kwargs={"pk": invoice_id}),
            {
                "amount": str(invoice_total),
                "payment_method_id": payment_method_id,
                "reference": "RCPT-1",
            },
            format="json",
        )
        self.assertEqual(payment_response.status_code, status.HTTP_201_CREATED)  # type: ignore[attr-defined]

        outstanding_response = self.client.get(reverse("reports-outstanding"), format="json")  # type: ignore[misc]
        self.assertEqual(outstanding_response.status_code, status.HTTP_200_OK)  # type: ignore[attr-defined]
        self.assertEqual(outstanding_response.data, [])  # type: ignore[attr-defined]

        report_response = self.client.get(reverse("reports-daily"), format="json")  # type: ignore[misc]
        self.assertEqual(report_response.status_code, status.HTTP_200_OK)  # type: ignore[attr-defined]
        self.assertEqual(report_response.data["total_invoices"], 1)  # type: ignore[index]

        webhook_response = self.client.post(  # type: ignore[misc]
            reverse("webhooks-pms"),
            {"event_type": "checkout", "folio_id": folio_id},
            format="json",
        )
        self.assertEqual(webhook_response.status_code, status.HTTP_202_ACCEPTED)  # type: ignore[attr-defined]