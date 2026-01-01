from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Sale, Invoice
from .utils import generate_invoice_pdf
import uuid

@receiver(post_save, sender=Sale)
def create_invoice(sender, instance, created, **kwargs):
    if created:
        # Check if invoice exists?
        if hasattr(instance, 'invoice'):
            return

        number = str(uuid.uuid4())[:8].upper()
        # Ensure uniqueness logic implies retry or better UUID usage
        
        invoice = Invoice.objects.create(sale=instance, number=number)
        
        # Generate PDF
        try:
            pdf_path = generate_invoice_pdf(invoice)
            invoice.pdf_file.name = pdf_path
            invoice.save()
        except Exception as e:
            print(f"Error generating PDF: {e}")
