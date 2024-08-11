from odoo import models, fields

class StockCategory(models.Model):
    _name = 'inventory.stock.category'
    _description = 'Stock Category'

    name = fields.Char(string='Nom de la Catégorie', required=True)
    description = fields.Text(string='Description')