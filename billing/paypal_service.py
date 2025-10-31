"""
PayPal Payment Integration Service
"""
import paypalrestsdk
from django.conf import settings
from decimal import Decimal


class PayPalService:
    """Service class for PayPal payment operations"""
    
    def __init__(self):
        """Initialize PayPal SDK with configuration"""
        paypalrestsdk.configure({
            "mode": settings.PAYPAL_MODE,
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_CLIENT_SECRET
        })
    
    def create_payment(self, invoice, return_url=None, cancel_url=None):
        """
        Create a PayPal payment for an invoice
        
        Args:
            invoice: Invoice object to create payment for
            return_url: URL to redirect after successful payment
            cancel_url: URL to redirect if payment is cancelled
            
        Returns:
            dict: Payment details including approval_url
        """
        if return_url is None:
            return_url = settings.PAYPAL_RETURN_URL
        if cancel_url is None:
            cancel_url = settings.PAYPAL_CANCEL_URL
        
        # Build line items from invoice
        items = []
        for line in invoice.lines.all():
            items.append({
                "name": line.description or "Hotel Charge",
                "sku": str(line.id),
                "price": str(line.net_amount),
                "currency": invoice.currency,
                "quantity": 1
            })
        
        # Calculate totals
        subtotal = str(invoice.subtotal)
        tax = str(invoice.tax_total)
        total = str(invoice.total)
        
        # Create payment object
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": return_url,
                "cancel_url": cancel_url
            },
            "transactions": [{
                "item_list": {
                    "items": items
                },
                "amount": {
                    "total": total,
                    "currency": invoice.currency,
                    "details": {
                        "subtotal": subtotal,
                        "tax": tax
                    }
                },
                "description": f"Invoice {invoice.invoice_number} - {invoice.folio.guest_name}",
                "invoice_number": invoice.invoice_number,
                "custom": str(invoice.id)  # Store invoice ID for reference
            }]
        })
        
        # Create the payment
        if payment.create():
            # Find approval URL
            approval_url = None
            for link in payment.links:
                if link.rel == "approval_url":
                    approval_url = link.href
                    break
            
            return {
                "success": True,
                "payment_id": payment.id,
                "approval_url": approval_url,
                "status": payment.state
            }
        else:
            return {
                "success": False,
                "error": payment.error
            }
    
    def execute_payment(self, payment_id, payer_id):
        """
        Execute (complete) a PayPal payment after user approval
        
        Args:
            payment_id: PayPal payment ID
            payer_id: Payer ID from PayPal redirect
            
        Returns:
            dict: Execution result
        """
        payment = paypalrestsdk.Payment.find(payment_id)
        
        if payment.execute({"payer_id": payer_id}):
            # Get transaction details
            transaction = payment.transactions[0]
            
            return {
                "success": True,
                "payment_id": payment.id,
                "state": payment.state,
                "amount": Decimal(transaction.amount.total),
                "currency": transaction.amount.currency,
                "payer_email": payment.payer.payer_info.email if hasattr(payment.payer.payer_info, 'email') else None,
                "transaction_id": transaction.related_resources[0].sale.id if transaction.related_resources else None,
                "invoice_id": int(transaction.custom) if transaction.custom else None
            }
        else:
            return {
                "success": False,
                "error": payment.error
            }
    
    def get_payment_details(self, payment_id):
        """
        Get details of a PayPal payment
        
        Args:
            payment_id: PayPal payment ID
            
        Returns:
            dict: Payment details
        """
        try:
            payment = paypalrestsdk.Payment.find(payment_id)
            transaction = payment.transactions[0] if payment.transactions else None
            
            return {
                "success": True,
                "payment_id": payment.id,
                "state": payment.state,
                "amount": Decimal(transaction.amount.total) if transaction else None,
                "currency": transaction.amount.currency if transaction else None,
                "create_time": payment.create_time,
                "update_time": payment.update_time,
                "invoice_id": int(transaction.custom) if transaction and transaction.custom else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def refund_payment(self, sale_id, amount=None):
        """
        Refund a PayPal payment
        
        Args:
            sale_id: PayPal sale/transaction ID
            amount: Amount to refund (None for full refund)
            
        Returns:
            dict: Refund result
        """
        try:
            sale = paypalrestsdk.Sale.find(sale_id)
            
            if amount:
                refund = sale.refund({
                    "amount": {
                        "total": str(amount),
                        "currency": sale.amount.currency
                    }
                })
            else:
                # Full refund
                refund = sale.refund({})
            
            if refund.success():
                return {
                    "success": True,
                    "refund_id": refund.id,
                    "state": refund.state,
                    "amount": Decimal(refund.amount.total) if hasattr(refund, 'amount') else amount
                }
            else:
                return {
                    "success": False,
                    "error": refund.error
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
