from reportlab.pdfgen import canvas
import os
from django.conf import settings

def generate_invoice_pdf(invoice):
    filename = f"invoice_{invoice.number}.pdf"
    directory = os.path.join(settings.MEDIA_ROOT, 'invoices')
    os.makedirs(directory, exist_ok=True)
    full_path = os.path.join(directory, filename)

    c = canvas.Canvas(full_path)
    
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, f"FACTURE #{invoice.number}")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, 780, f"Boutique: {invoice.sale.shop.name}")
    c.drawString(50, 760, f"Date: {invoice.sale.created_at.strftime('%d/%m/%Y %H:%M')}")
    
    # Items
    y = 720
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Produit")
    c.drawString(300, y, "Qté")
    c.drawString(350, y, "Prix")
    c.drawString(450, y, "Total")
    
    y -= 20
    c.setFont("Helvetica", 12)
    
    for item in invoice.sale.items.all():
        c.drawString(50, y, item.product_name[:30])
        c.drawString(300, y, str(item.quantity))
        c.drawString(350, y, str(item.price))
        c.drawString(450, y, str(item.subtotal))
        y -= 20
        
    # Total
    c.setFont("Helvetica-Bold", 14)
    c.drawString(350, y-30, "TOTAL:")
    c.drawString(450, y-30, str(invoice.sale.total_amount))
    
    c.save()
    
    return f"invoices/{filename}"
