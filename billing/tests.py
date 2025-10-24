from datetime import timedeltafrom datetime import timedelta

from decimal import Decimalfrom decimal import Decimal

from typing import cast

from django.contrib.auth import get_user_model

from django.contrib.auth import get_user_modelfrom django.utils import timezone

from django.utils import timezonefrom rest_framework import status

from rest_framework import statusfrom rest_framework.reverse import reverse

from rest_framework.reverse import reversefrom rest_framework.response import Response

from rest_framework.response import Responsefrom rest_framework.test import APITestCase

from rest_framework.test import APITestCase



class BillingApiTests(APITestCase):

class BillingApiTests(APITestCase):	def setUp(self) -> None:

    def setUp(self) -> None:		User = get_user_model()

        User = get_user_model()		self.admin = User.objects.create_superuser(

        self.admin = User.objects.create_superuser(			username="admin",

            username="admin",			email="admin@example.com",

            email="admin@example.com",			password="Str0ngPass!",

            password="Str0ngPass!",		)

        )		self.client.force_authenticate(user=self.admin)

        self.client.force_authenticate(user=self.admin)

	def test_end_to_end_invoice_flow(self) -> None:

    def test_end_to_end_invoice_flow(self) -> None:		guest_response: Response = self.client.post(

        guest_response = cast(			reverse("guest-list"),

            Response,			{

            self.client.post(				"first_name": "John",

                reverse("guest-list"),				"last_name": "Doe",

                {				"email": "john@example.com",

                    "first_name": "John",				"phone_number": "1234567890",

                    "last_name": "Doe",				"company_name": "Test Corp",

                    "email": "john@example.com",			},

                    "phone_number": "1234567890",			format="json",

                    "company_name": "Test Corp",		)

                },		self.assertEqual(guest_response.status_code, status.HTTP_201_CREATED)

                format="json",		guest_id = guest_response.data["id"]

            ),

        )		today = timezone.now().date()

        self.assertEqual(guest_response.status_code, status.HTTP_201_CREATED)		reservation_response: Response = self.client.post(

        guest_id = guest_response.data["id"]			reverse("reservation-list"),

			{

        today = timezone.now().date()				"guest_id": guest_id,

        reservation_response = cast(				"reservation_number": "RES-1001",

            Response,				"status": "booked",

            self.client.post(				"check_in": today.isoformat(),

                reverse("reservation-list"),				"check_out": (today + timedelta(days=2)).isoformat(),

                {				"room_number": "101",

                    "guest_id": guest_id,				"rate_plan": "BAR",

                    "reservation_number": "RES-1001",				"number_of_guests": 2,

                    "status": "booked",				"notes": "VIP",

                    "check_in": today.isoformat(),			},

                    "check_out": (today + timedelta(days=2)).isoformat(),			format="json",

                    "room_number": "101",		)

                    "rate_plan": "BAR",		self.assertEqual(reservation_response.status_code, status.HTTP_201_CREATED)

                    "number_of_guests": 2,		reservation_id = reservation_response.data["id"]

                    "notes": "VIP",

                },		folio_response: Response = self.client.post(

                format="json",			reverse("folio-list"),

            ),			{

        )				"guest_name": "John Doe",

        self.assertEqual(reservation_response.status_code, status.HTTP_201_CREATED)				"reservation_id": reservation_id,

        reservation_id = reservation_response.data["id"]				"currency": "USD",

				"status": "open",

        folio_response = cast(				"notes": "Room folio",

            Response,			},

            self.client.post(			format="json",

                reverse("folio-list"),		)

                {		self.assertEqual(folio_response.status_code, status.HTTP_201_CREATED)

                    "guest_name": "John Doe",		folio_id = folio_response.data["id"]

                    "reservation_id": reservation_id,

                    "currency": "USD",		item_response: Response = self.client.post(

                    "status": "open",			reverse("folio-add-item", kwargs={"pk": folio_id}),

                    "notes": "Room folio",			{

                },				"description": "Room Night",

                format="json",				"item_type": "room",

            ),				"quantity": "2",

        )				"unit_price": "150.00",

        self.assertEqual(folio_response.status_code, status.HTTP_201_CREATED)			},

        folio_id = folio_response.data["id"]			format="json",

		)

        item_response = cast(		self.assertEqual(item_response.status_code, status.HTTP_201_CREATED)

            Response,

            self.client.post(		discount_response: Response = self.client.post(

                reverse("folio-add-item", kwargs={"pk": folio_id}),			reverse("discount-list"),

                {			{

                    "description": "Room Night",				"name": "VIP Discount",

                    "item_type": "room",				"discount_type": "percentage",

                    "quantity": "2",				"value": "10.00",

                    "unit_price": "150.00",				"is_active": True,

                },			},

                format="json",			format="json",

            ),		)

        )		self.assertEqual(discount_response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(item_response.status_code, status.HTTP_201_CREATED)		discount_id = discount_response.data["id"]



        discount_response = cast(		payment_method_response: Response = self.client.post(

            Response,			reverse("config-payment-method-list"),

            self.client.post(			{"name": "Cash", "is_active": True, "requires_reference": False},

                reverse("discount-list"),			format="json",

                {		)

                    "name": "VIP Discount",		self.assertEqual(payment_method_response.status_code, status.HTTP_201_CREATED)

                    "discount_type": "percentage",		payment_method_id = payment_method_response.data["id"]

                    "value": "10.00",

                    "is_active": True,		invoice_response: Response = self.client.post(

                },			reverse("invoice-list"),

                format="json",			{

            ),				"folio_id": folio_id,

        )				"discount_ids": [discount_id],

        self.assertEqual(discount_response.status_code, status.HTTP_201_CREATED)				"notes": "Checkout invoice",

        discount_id = discount_response.data["id"]			},

			format="json",

        payment_method_response = cast(		)

            Response,		self.assertEqual(invoice_response.status_code, status.HTTP_201_CREATED)

            self.client.post(		invoice_id = invoice_response.data["id"]

                reverse("config-payment-method-list"),		invoice_total = Decimal(invoice_response.data["total"])

                {"name": "Cash", "is_active": True, "requires_reference": False},

                format="json",		payment_response: Response = self.client.post(

            ),			reverse("invoice-create-payment", kwargs={"pk": invoice_id}),

        )			{

        self.assertEqual(payment_method_response.status_code, status.HTTP_201_CREATED)				"amount": str(invoice_total),

        payment_method_id = payment_method_response.data["id"]				"payment_method_id": payment_method_id,

				"reference": "RCPT-1",

        invoice_response = cast(			},

            Response,			format="json",

            self.client.post(		)

                reverse("invoice-list"),		self.assertEqual(payment_response.status_code, status.HTTP_201_CREATED)

                {

                    "folio_id": folio_id,		outstanding_response: Response = self.client.get(

                    "discount_ids": [discount_id],			reverse("reports-outstanding"), format="json"

                    "notes": "Checkout invoice",		)

                },		self.assertEqual(outstanding_response.status_code, status.HTTP_200_OK)

                format="json",		self.assertEqual(outstanding_response.data, [])

            ),

        )		report_response: Response = self.client.get(reverse("reports-daily"), format="json")

        self.assertEqual(invoice_response.status_code, status.HTTP_201_CREATED)		self.assertEqual(report_response.status_code, status.HTTP_200_OK)

        invoice_id = invoice_response.data["id"]		self.assertEqual(report_response.data["total_invoices"], 1)

        invoice_total = Decimal(invoice_response.data["total"])

		webhook_response: Response = self.client.post(

        payment_response = cast(			reverse("webhooks-pms"),

            Response,			{"event_type": "checkout", "folio_id": folio_id},

            self.client.post(			format="json",

                reverse("invoice-create-payment", kwargs={"pk": invoice_id}),		)

                {		self.assertEqual(webhook_response.status_code, status.HTTP_202_ACCEPTED)

                    "amount": str(invoice_total),
                    "payment_method_id": payment_method_id,
                    "reference": "RCPT-1",
                },
                format="json",
            ),
        )
        self.assertEqual(payment_response.status_code, status.HTTP_201_CREATED)

        outstanding_response = cast(
            Response,
            self.client.get(reverse("reports-outstanding"), format="json"),
        )
        self.assertEqual(outstanding_response.status_code, status.HTTP_200_OK)
        self.assertEqual(outstanding_response.data, [])

        report_response = cast(
            Response,
            self.client.get(reverse("reports-daily"), format="json"),
        )
        self.assertEqual(report_response.status_code, status.HTTP_200_OK)
        self.assertEqual(report_response.data["total_invoices"], 1)

        webhook_response = cast(
            Response,
            self.client.post(
                reverse("webhooks-pms"),
                {"event_type": "checkout", "folio_id": folio_id},
                format="json",
            ),
        )
        self.assertEqual(webhook_response.status_code, status.HTTP_202_ACCEPTED)
