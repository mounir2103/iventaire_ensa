from odoo import models, fields

class StockSupplier(models.Model):
    _name = 'inventory.stock.supplier'
    _description = 'Stock Supplier'

    name = fields.Char(string='Nom du fournisseur', required=True)
    contact_name = fields.Char(string='Personne à Contacter')
    contact_email = fields.Char(string='Email')
    contact_phone = fields.Char(string='Téléphone')
    address = fields.Text(string='Addresse')