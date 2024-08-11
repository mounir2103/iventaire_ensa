import base64
from io import BytesIO
import qrcode
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StockItem(models.Model):
    _name = 'inventory.stock.item'
    _description = 'Stock Item'

    name = fields.Char(string='Nom de l\'article', required=True)
    category_id = fields.Many2one('inventory.stock.category', string='Categorie', required=True)
    quantity_available = fields.Integer(string='Quantité Disponible', compute='_compute_quantity_available', store=True)
    supplier_id = fields.Many2one('inventory.stock.supplier', string='Fournisseur')
    description = fields.Text(string='Description')
    year = fields.Date(string='Date d\'acquisition')
    location = fields.Char(string='Local')
    value = fields.Float(string='Valeur')
    market_number = fields.Char(string='Numéro de marché')
    qr_code_image = fields.Binary(string='QR Code Image', readonly=True)
    qr_code_pdf_file = fields.Binary(string='QR Code PDF', readonly=True)
    new_quantity = fields.Integer(string='Nouvelle Quantité', default=0)

    movement_ids = fields.One2many('inventory.stock.movement', 'item_id', string='Mouvements')

    @api.depends('movement_ids')
    def _compute_quantity_available(self):
        for record in self:
            total_entrees = sum(record.movement_ids.filtered(lambda m: m.movement_type == 'entrée').mapped('quantity'))
            total_sorties = sum(record.movement_ids.filtered(lambda m: m.movement_type == 'sortie').mapped('quantity'))
            total_emprunts = sum(record.movement_ids.filtered(lambda m: m.movement_type == 'emprunt').mapped('quantity'))
            total_retours = sum(record.movement_ids.filtered(lambda m: m.movement_type == 'retour').mapped('quantity'))
            record.quantity_available = total_entrees - total_sorties - total_emprunts + total_retours

    @api.model
    def create(self, vals):
        record = super(StockItem, self).create(vals)
        record._create_stock_movement(vals.get('new_quantity', 0))
        record.generate_qr_code()
        return record

    def write(self, vals):
        if 'new_quantity' in vals:
            new_quantity = vals['new_quantity']
            if new_quantity > self.quantity_available:
                # Update quantity available with the new quantity
                self._create_stock_movement(new_quantity - self.quantity_available)
            elif new_quantity < self.quantity_available:
                # Update quantity available with the new quantity
                self._create_stock_movement(-(self.quantity_available - new_quantity))
        result = super(StockItem, self).write(vals)
        if 'name' in vals or 'year' in vals or 'market_number' in vals or 'location' in vals:
            self.generate_qr_code()
        return result

    def _create_stock_movement(self, quantity_change):
        if quantity_change != 0:
            movement_type = 'entrée' if quantity_change > 0 else 'sortie'
            self.env['inventory.stock.movement'].create({
                'item_id': self.id,
                'quantity': abs(quantity_change),
                'movement_type': movement_type,
                'movement_date': fields.Date.today(),
                'category_id': self.category_id.id,
            })

    def generate_qr_code(self):
        qr_data = f"Nom: {self.name}\nAnnée: {self.year}\nNuméro de marché: {self.market_number}\nLocation: {self.location}"

        # Generate QR Code Image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')

        # Convert to image and store in qr_code_image
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        self.qr_code_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # Save QR Code to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            img.save(temp_file, format='PNG')
            temp_file_path = temp_file.name

        # Generate PDF with only the QR code
        buffer_pdf = BytesIO()
        c = canvas.Canvas(buffer_pdf, pagesize=letter)
        c.drawImage(temp_file_path, 100, 600, width=200, height=200)  # Position and size of QR code in PDF
        c.showPage()
        c.save()
        buffer_pdf.seek(0)
        self.qr_code_pdf_file = base64.b64encode(buffer_pdf.getvalue()).decode('utf-8')