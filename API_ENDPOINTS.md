# Hotel Billing API - Complete Endpoint Reference

## 🔐 Authentication Endpoints

### 1. Obtain JWT Token (Login)
- **POST** `/api/auth/login`
- **Body**: `{"username": "your_username", "password": "your_password"}`
- **Response**: `{"access": "...", "refresh": "..."}`

### 2. Refresh JWT Token
- **POST** `/api/auth/refresh`
- **Body**: `{"refresh": "your_refresh_token"}`
- **Response**: `{"access": "new_access_token"}`

---

## 👤 User Management

### 3. List Users
- **GET** `/api/users/`
- **Permission**: Admin only

### 4. Create User
- **POST** `/api/users/`
- **Permission**: Admin only

### 5. Retrieve User
- **GET** `/api/users/{id}/`
- **Permission**: Admin only

### 6. Update User
- **PUT/PATCH** `/api/users/{id}/`
- **Permission**: Admin only

### 7. Delete User
- **DELETE** `/api/users/{id}/`
- **Permission**: Admin only

---

## 🏨 Guest Management

### 8. List Guests
- **GET** `/api/guests/`
- **Query Params**: `?search=name/email/phone`

### 9. Create Guest
- **POST** `/api/guests/`
- **Body**: `{"name": "John Doe", "email": "john@example.com", "phone": "+1234567890"}`

### 10. Retrieve Guest
- **GET** `/api/guests/{id}/`

### 11. Update Guest
- **PUT/PATCH** `/api/guests/{id}/`

### 12. Delete Guest
- **DELETE** `/api/guests/{id}/`

---

## 📅 Reservation Management

### 13. List Reservations
- **GET** `/api/reservations/`
- **Query Params**: `?status=booked/checked_in/checked_out/cancelled&search=confirmation_number`

### 14. Create Reservation
- **POST** `/api/reservations/`
- **Body**: 
```json
{
  "guest_id": 1,
  "room_number": "101",
  "check_in_date": "2025-10-25",
  "check_out_date": "2025-10-27",
  "guest_count": 2,
  "status": "booked"
}
```

### 15. Retrieve Reservation
- **GET** `/api/reservations/{id}/`

### 16. Update Reservation
- **PUT/PATCH** `/api/reservations/{id}/`

### 17. Delete Reservation
- **DELETE** `/api/reservations/{id}/`

---

## 📋 Folio Management

### 18. List Folios
- **GET** `/api/folios/`
- **Query Params**: `?status=open/closed&search=guest_name`

### 19. Create Folio
- **POST** `/api/folios/`
- **Body**: 
```json
{
  "reservation_id": 1,
  "guest_name": "John Doe",
  "status": "open"
}
```

### 20. Retrieve Folio
- **GET** `/api/folios/{id}/`

### 21. Update Folio
- **PUT/PATCH** `/api/folios/{id}/`

### 22. Delete Folio
- **DELETE** `/api/folios/{id}/`

### 23. Add Item to Folio
- **POST** `/api/folios/{id}/items`
- **Body**: 
```json
{
  "item_type": "room_charge",
  "description": "Room 101 - Nightly Rate",
  "quantity": 1,
  "unit_price": "150.00",
  "tax_rule_id": 1
}
```

### 24. Update Folio Item
- **PUT** `/api/folios/{id}/items/{item_id}`
- **Body**: 
```json
{
  "quantity": 2,
  "unit_price": "175.00"
}
```

---

## 🧾 Invoice Management

### 25. List Invoices
- **GET** `/api/invoices/`
- **Query Params**: `?status=draft/issued/paid/cancelled&search=invoice_number`

### 26. Create Invoice from Folio
- **POST** `/api/invoices/`
- **Body**: 
```json
{
  "folio_id": 1,
  "discount_ids": [1, 2]
}
```

### 27. Retrieve Invoice
- **GET** `/api/invoices/{id}/`

### 28. Update Invoice
- **PUT/PATCH** `/api/invoices/{id}/`

### 29. Delete Invoice
- **DELETE** `/api/invoices/{id}/`

### 30. Generate Invoice PDF
- **GET** `/api/invoices/{id}/pdf`
- **Response**: PDF file download

### 31. Create Credit Note
- **POST** `/api/invoices/{id}/credit_note`
- **Body**: 
```json
{
  "reason": "Service credit",
  "amount": "50.00"
}
```

### 32. Create Debit Note
- **POST** `/api/invoices/{id}/debit_note`
- **Body**: 
```json
{
  "reason": "Additional charges",
  "amount": "25.00"
}
```

### 33. Create Payment for Invoice
- **POST** `/api/invoices/{id}/create_payment`
- **Body**: 
```json
{
  "payment_method_id": 1,
  "amount": "200.00",
  "reference": "CC-1234"
}
```

---

## 💰 Payment Management

### 34. List Payments
- **GET** `/api/payments/`
- **Query Params**: `?status=posted/voided/refunded`

### 35. Create Payment
- **POST** `/api/payments/`
- **Body**: 
```json
{
  "invoice_id": 1,
  "payment_method_id": 1,
  "amount": "200.00",
  "reference": "CC-1234"
}
```

### 36. Retrieve Payment
- **GET** `/api/payments/{id}/`

### 37. Update Payment
- **PUT/PATCH** `/api/payments/{id}/`

### 38. Delete Payment
- **DELETE** `/api/payments/{id}/`

### 39. Refund Payment
- **POST** `/api/payments/{id}/refund`
- **Body**: 
```json
{
  "amount": "50.00",
  "reason": "Customer refund request"
}
```

---

## 🎫 Discount Management

### 40. List Discounts
- **GET** `/api/discounts/`
- **Query Params**: `?is_active=true&discount_type=percentage/fixed&search=name`

### 41. Create Discount
- **POST** `/api/discounts/`
- **Body**: 
```json
{
  "name": "Weekend Special",
  "discount_type": "percentage",
  "value": "15.00",
  "is_active": true
}
```

---

## 🏢 Corporate Account Management

### 42. List Corporate Accounts
- **GET** `/api/corporate-accounts/`
- **Query Params**: `?search=name/code`

### 43. Create Corporate Account
- **POST** `/api/corporate-accounts/`
- **Body**: 
```json
{
  "name": "Acme Corp",
  "code": "ACME001",
  "payment_terms_days": 30,
  "credit_limit": "10000.00"
}
```

### 44. Retrieve Corporate Account
- **GET** `/api/corporate-accounts/{id}/`

### 45. Update Corporate Account
- **PUT/PATCH** `/api/corporate-accounts/{id}/`

### 46. Delete Corporate Account
- **DELETE** `/api/corporate-accounts/{id}/`

### 47. List Corporate Account Invoices
- **GET** `/api/corporate-accounts/{id}/invoices`

---

## 📊 Tax Rule Management

### 48. List Tax Rules
- **GET** `/api/tax-rules/`
- **Permission**: Admin only

### 49. Create Tax Rule
- **POST** `/api/tax-rules/`
- **Permission**: Admin only
- **Body**: 
```json
{
  "name": "Sales Tax",
  "rate": "8.50",
  "is_active": true
}
```

### 50. Retrieve Tax Rule
- **GET** `/api/tax-rules/{id}/`
- **Permission**: Admin only

### 51. Update Tax Rule
- **PUT/PATCH** `/api/tax-rules/{id}/`
- **Permission**: Admin only

### 52. Delete Tax Rule
- **DELETE** `/api/tax-rules/{id}/`
- **Permission**: Admin only

---

## 💳 Payment Method Management

### 53. List Payment Methods
- **GET** `/api/payment-methods/`
- **Permission**: Admin only

### 54. Create Payment Method
- **POST** `/api/payment-methods/`
- **Permission**: Admin only
- **Body**: 
```json
{
  "name": "Visa Credit Card",
  "code": "VISA",
  "is_active": true
}
```

### 55. Retrieve Payment Method
- **GET** `/api/payment-methods/{id}/`
- **Permission**: Admin only

### 56. Update Payment Method
- **PUT/PATCH** `/api/payment-methods/{id}/`
- **Permission**: Admin only

### 57. Delete Payment Method
- **DELETE** `/api/payment-methods/{id}/`
- **Permission**: Admin only

---

## 📈 Reports

### 58. Daily Revenue Report
- **GET** `/api/reports/daily`
- **Query Params**: `?date=2025-10-24` (defaults to today)
- **Response**: Total invoices, revenue, and payments for the date

### 59. Tax Summary Report
- **GET** `/api/reports/tax-summary`
- **Query Params**: `?start_date=2025-10-01&end_date=2025-10-31`
- **Response**: Tax breakdown by tax rule

### 60. Outstanding Invoices Report
- **GET** `/api/reports/outstanding`
- **Response**: All invoices with outstanding balances

---

## 🔔 Webhook Endpoints

### 61. PMS Webhook
- **POST** `/api/webhooks/pms`
- **Permission**: Public (AllowAny)
- **Body**: Any JSON payload with `event_type` field

### 62. POS Webhook
- **POST** `/api/webhooks/pos`
- **Permission**: Public (AllowAny)
- **Body**: Any JSON payload with `event_type` field

### 63. Payment Gateway Webhook
- **POST** `/api/webhooks/payment-gateway`
- **Permission**: Public (AllowAny)
- **Body**: Any JSON payload with `event_type` field

---

## 📖 API Documentation

### 64. Swagger UI (Interactive Testing)
- **URL**: http://127.0.0.1:8000/api/docs/
- **Features**: Test all endpoints directly in browser

### 65. ReDoc (API Documentation)
- **URL**: http://127.0.0.1:8000/api/redoc/
- **Features**: Beautiful, readable API documentation

### 66. OpenAPI Schema (JSON)
- **URL**: http://127.0.0.1:8000/api/schema/
- **Features**: Machine-readable API schema

---

## 🔧 Testing with cURL

### Example: Login
```powershell
curl -X POST http://127.0.0.1:8000/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{\"username\":\"admin\",\"password\":\"your_password\"}'
```

### Example: Create Guest (with token)
```powershell
curl -X POST http://127.0.0.1:8000/api/guests/ `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" `
  -d '{\"name\":\"Jane Smith\",\"email\":\"jane@example.com\",\"phone\":\"+1987654321\"}'
```

### Example: Get Daily Report
```powershell
curl -X GET "http://127.0.0.1:8000/api/reports/daily?date=2025-10-24" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## ✅ All API Endpoints Summary

**Total Endpoints**: 66 (including 3 documentation endpoints)

**By Category**:
- Authentication: 2
- User Management: 5
- Guest Management: 5
- Reservation Management: 5
- Folio Management: 7
- Invoice Management: 9
- Payment Management: 6
- Discount Management: 2
- Corporate Account Management: 6
- Tax Rule Management: 5
- Payment Method Management: 5
- Reports: 3
- Webhooks: 3
- Documentation: 3

**Status**: ✅ All endpoints functional and properly documented in OpenAPI schema

**No drf-spectacular warnings** - Clean schema generation! 🎉
