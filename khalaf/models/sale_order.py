# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from email.policy import default

from odoo import fields, models, _

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('insta', 'InstaPay'),
        ('voda', 'Vodafone'),
        ('visa', 'Visa'),
        ('flash', 'Flash')
        ], string="Payment Method", help="Indicates if payment was made by cash , visa or any.",default='cash')

    collection_status = fields.Selection([('collected', 'Collected'),('not_collected', 'Not Collected')],default='not_collected', string="Collection Status")


