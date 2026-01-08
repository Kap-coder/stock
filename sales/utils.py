from django.template.loader import get_template
from xhtml2pdf import pisa
import os
from django.conf import settings
from django.utils import timezone
from .models import ActionLog


def generate_invoice_pdf(invoice):
    """Render invoice to PDF using HTML template (xhtml2pdf) and save to media/invoices."""
    template = get_template('sales/invoice_pdf.html')
    context = {
        'invoice': invoice,
        'sale': invoice.sale,
        'items': invoice.sale.items.all(),
        'shop': invoice.sale.shop,
    }

    html = template.render(context)

    filename = f"invoice_{invoice.number}.pdf"
    directory = os.path.join(settings.MEDIA_ROOT, 'invoices')
    os.makedirs(directory, exist_ok=True)
    full_path = os.path.join(directory, filename)

    with open(full_path, 'wb') as f:
        pisa_status = pisa.CreatePDF(html, dest=f)
        if pisa_status.err:
            raise Exception('Error creating PDF')
    # log action
    try:
        ActionLog.objects.create(
            shop=invoice.sale.shop,
            user=getattr(invoice.sale, 'cashier', None),
            action=ActionLog.ActionChoices.INVOICE_PDF_GENERATED,
            object_type='Invoice',
            object_id=str(invoice.id),
            description=f'PDF generated: {filename}',
        )
    except Exception:
        pass

    return f'invoices/{filename}'
