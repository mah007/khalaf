#
from odoo import api, fields, models



class Partner(models.Model):
    _inherit = "res.partner"


    mobile2 = fields.Char(unaccent=False)
    mobile3 = fields.Char(unaccent=False)
    mobile4 = fields.Char(unaccent=False)


