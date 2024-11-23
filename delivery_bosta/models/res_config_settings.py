# -*- coding: utf-8 -*-


##############################################################################
#
#
#    Copyright (C) 2020-TODAY .
#    Author: Eng.Ramadan Khalil (<rkhalil1990@gmail.com>)
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
##############################################################################

from odoo import fields, models, api, _
import json
import requests


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_delivery_bosta = fields.Boolean("Bosta")


    bosta_api_key = fields.Char('Bosta API Key')
    bosta_api_url = fields.Char('Bosta API URL')
    bosta_tracking_endpoint = fields.Char('Bosta Tracking EndPoint')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ir_config = self.env['ir.config_parameter'].sudo()
        bosta_api_key = ir_config.get_param('bosta_api_key',
                                            default='')
        bosta_api_url = ir_config.get_param('bosta_api_url',
                                            default='')
        bosta_tracking_endpoint = ir_config.get_param('bosta_tracking_endpoint',
                                                      default='')

        res.update(
            bosta_api_key=bosta_api_key,
            bosta_api_url=bosta_api_url,
            bosta_tracking_endpoint=bosta_tracking_endpoint,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ir_config = self.env['ir.config_parameter'].sudo()
        ir_config.set_param("bosta_api_key", self.bosta_api_key or "")
        ir_config.set_param("bosta_api_url", self.bosta_api_url or "")
        ir_config.set_param("bosta_tracking_endpoint",
                            self.bosta_tracking_endpoint or "")
