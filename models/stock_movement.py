from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class InventoryStockMovement(models.Model):
    _name = 'inventory.stock.movement'
    _description = 'Inventory Stock Movement'

    item_id = fields.Many2one('inventory.stock.item', string="Article", required=True)
    quantity = fields.Integer(string="Quantité", required=True)
    movement_type = fields.Selection([
        ('entrée', 'Entrée'),
        ('sortie', 'Sortie'),
        ('emprunt', 'Emprunt'),
        ('retour', 'Retour')
    ], string="Type de transaction", required=True)
    movement_date = fields.Date(string="Date", default=fields.Date.today)

    @api.onchange('category_id')
    def _onchange_category_id(self):
        if not self.category_id:
            self.item_id = None  # Réinitialiser l'article lié si la catégorie est vide

    @api.onchange('item_id')
    def _onchange_item_id(self):
        if not self.item_id:
            self.quantity = 0  # Réinitialise la quantité si l'article est vide
        _logger.info("Item ID: %s", self.item_id.id if self.item_id else 'None')

    @api.model
    def create(self, vals):
        # Vérifications des contraintes et validations
        if 'item_id' in vals:
            item = self.env['inventory.stock.item'].browse(vals['item_id'])
            if not item.exists():
                raise ValidationError("L'article spécifié n'existe pas.")

            # Gestion des quantités selon le type de mouvement
            if vals['movement_type'] in ['sortie', 'emprunt']:
                if vals['quantity'] > item.quantity_available:
                    raise ValidationError("La quantité demandée est supérieure à la quantité disponible.")

        # Création du mouvement
        record = super(InventoryStockMovement, self).create(vals)

        # Mise à jour des quantités
        record.item_id._compute_quantity_available()

        return record

    def write(self, vals):
        # Vérifications des contraintes et validations
        if 'item_id' in vals:
            item = self.env['inventory.stock.item'].browse(vals['item_id'])
            if not item.exists():
                raise ValidationError("L'article spécifié n'existe pas.")

            # Gestion des quantités selon le type de mouvement
            if 'movement_type' in vals and vals['movement_type'] in ['sortie', 'emprunt']:
                if vals['quantity'] > item.quantity_available:
                    raise ValidationError("La quantité demandée est supérieure à la quantité disponible.")

        # Mise à jour des quantités
        result = super(InventoryStockMovement, self).write(vals)
        if 'item_id' in vals:
            self.item_id._compute_quantity_available()

        return result