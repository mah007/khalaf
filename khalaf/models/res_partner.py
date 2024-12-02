#
from odoo import api, fields, models, tools, SUPERUSER_ID, _, Command



class Partner(models.Model):
    _inherit = "res.partner"


    mobile2 = fields.Char('mobile 2')
    mobile3 = fields.Char('mobile 3')
    mobile4 = fields.Char('mobile 3')


