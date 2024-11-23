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
from odoo.exceptions import ValidationError, UserError

import json
import requests

BOSTA_SHIPEMENT_TYPES = {'forward': 10,
                         'exchange': 30,
                         'crp': 25,
                         'cc': 15}

base_url = 'https://api.bosta.co/api/v0'
bosta_tracking_link = "https://bosta.co/index.php/tracking-shipment/?track_num="


class BostaStatePrice(models.Model):
    _name = 'bosta.price'

    state = fields.Many2one('res.country.state',
                            domain=[('country_id.code', '=', 'EG')],
                            string='City')
    price = fields.Float(string="Price")
    carrier_id = fields.Many2one('delivery.carrier')


class BostaTrackingStatus(models.Model):
    _name = 'bosta.status'

    name = fields.Char(string="Status Name",
                       help="Status to no longer be updated by cron job")


class ProviderBosta(models.Model):
    _inherit = 'delivery.carrier'

    bosta_api_key = fields.Char('Bosta API Key')
    bosta_api_url = fields.Char('Bosta API URL')
    bosta_tracking_endpoint = fields.Char('Bosta Tracking EndPoint')

    delivery_type = fields.Selection(selection_add=[('bosta', 'Bosta')],
                                     ondelete={'bosta': 'set default'})
    delivery_service = fields.Selection(selection=[('cash', 'Cash Collection'),
                                                   ('package',
                                                    'Package Delivery')],
                                        default='package')
    bosta_shipment_type = fields.Selection(string="Shipment Type",
                                           selection=[('forward', 'Forward'),
                                                      ('exchange', 'Exchange'),
                                                      ('cc', 'Cash Collect'),
                                                      ('crp',
                                                       'Customer Return Pickup CRP')])

    bosta_price = fields.One2many('bosta.price', inverse_name='carrier_id')
    bosta_delivery_note = fields.Text('Bosta Delivery Note')

    def create_shipment(self):
        ctx = dict(self._context)
        if "vals_for_shipping" not in ctx:
            return None
        delivery_vals = ctx.get('vals_for_shipping')
        receiver = {
            'firstName': delivery_vals.get('receiver_firstname', ''),
            'lastName': delivery_vals.get('receiver_lastname', ''),
            'email': delivery_vals.get('receiver_email', ''),
            'phone': delivery_vals.get('receiver_phone', '')
        }

        pickup_address = {
            'firstLine': delivery_vals.get('pickup_street1', ''),
            'secondLine': '{} {}'.format(
                delivery_vals.get('pickup_street2', ''),
                delivery_vals.get('pickup_zone', '')),
            'zone': delivery_vals.get('pickup_zone', ''),
            'city': delivery_vals.get('pickup_city_code', '')
        }

        dropoff_address = {
            'firstLine': delivery_vals.get('receiver_street1', ''),
            'secondLine': '{} {}'.format(
                delivery_vals.get('receiver_street2', '')
                , delivery_vals.get('receiver_zone', '')),
            'zone': delivery_vals.get('receiver_zone', ''),
            'city': delivery_vals.get('receiver_city_code', '')
        }
        item_count = 0
        shipment_data = ctx.get("vals_for_shipping")
        picking_id = shipment_data.get('picking_id')
        if picking_id:
            item_count = sum(
                [m.product_uom_qty for m in picking_id.move_ids if
                 m.product_id.detailed_type == 'product'])

        package_details = {
            "itemsCount": item_count,
            "document": "Document",
            "description": shipment_data.get('notes')
        }
        shipment_type = BOSTA_SHIPEMENT_TYPES.get(self.bosta_shipment_type,
                                                  False)
        if not shipment_type:
            raise ValidationError(_('Please set bosta shipment type'))
        delivery_note = delivery_vals.get('notes', '')

        return {
            "specs": {
                "size": "SMALL",
                "packageDetails": package_details
            },
            'pickupAddress': pickup_address,
            'dropOffAddress': dropoff_address,
            'receiver': receiver,
            'notes': delivery_note,
            'cod': delivery_vals.get('cod_amount', ''),
            'type': shipment_type,
            'businessReference': delivery_vals.get('businessReference', ''),
            'allowToOpenPackage': delivery_vals.get('allow_open_package', '')
        }

    def bosta_send_shipping(self, picking):
        error_msg = ""
        api_key = self.bosta_api_key
        shipment = self.create_shipment()
        if not shipment:
            return None
        encoded_data = json.dumps(shipment, ensure_ascii=False).encode('utf-8')
        if not api_key:
            raise ValidationError('Please Provide API Key For Bosta Delivery')

        result = requests.post(base_url + '/deliveries', json=shipment,
                               headers={'Authorization': api_key})

        if result.status_code in [200, 201]:
            result = result.json()
        else:
            error_msg = 'Failed to send shipment to Bosta due to the following error \n Eror code : {} \n Error Message : {}'.format(
                result.status_code, result.content)

        if error_msg:
            raise ValidationError(error_msg)

        res = {
            'tracking_number': result['trackingNumber'],
            'delivery_id': result['_id'],
            'status': self.get_status_by_code(result['state']['code']),
            # 'exact_price': picking.sale_id.delivery_price
        }
        return res

    def bosta_rate_shipment(self, order):
        customer = order.partner_id
        city = self.get_city_code(customer.state_id.code)
        res_price = 0
        if not city:
            response = {
                "price": self.product_id.lst_price or 0,
                "error_message": "Bosta doesnt not ship to/from " + str(
                    customer.state_id.name),
                "warning_message": None,
                "success": False,
            }
        else:
            prices = self.bosta_price
            for price in prices:
                if price.state == customer.state_id:
                    res_price = price.price
                    break
            if not res_price:
                response = {
                    "price": self.product_id.lst_price or 0,
                    "error_message": None,
                    "warning_message": "No price set for customer location, using product price",
                    "success": True
                }
            else:
                response = {
                    "price": res_price,
                    "error_message": None,
                    "warning_message": None,
                    "success": True,
                }
        return response

    def bosta_get_awb(self, id):
        api_key = self.bosta_api_key
        if not api_key:
            raise UserError('Please Add Bosta API Key To Bosta Delivey')
        response = requests.get(base_url + '/deliveries/awb/' + id,
                                headers={'Authorization': api_key})
        if response.status_code == 200:
            response = response.json()
        else:
            return None
        return response['data']

    def bosta_get_status(self, id):
        api_key = self.bosta_api_key
        if not api_key:
            raise UserError('Please Add Bosta API Key To Bosta Delivey')

        response = requests.get(base_url + '/deliveries/' + str(id),
                                headers={'Authorization': api_key})

        if response.status_code == 200:
            response = response.json()
        elif response.status_code == 500 or response.status_code == 502:
            return None
        else:
            return None

        if response.get('state'):
            if type(response.get('state')) is dict:
                if response['state'].get('value', False):
                    return response['state'].get('value', False)
                elif response['state'].get('code', False):
                    return self.get_status_by_code(
                        response['state']['code'])
            elif type(response.get('state')) is str:
                return response.get('state')

        return 'Returned to Shipper'

    @api.model
    def get_status_by_code(self, code):
        return {
            10: 'Pending',
            15: 'In progress',
            16: 'Delivery on route',
            20: 'Picking up',
            21: 'Picking up from warehouse',
            22: 'Arrived at warehouse',
            23: 'Received at warehouse',
            25: 'Arrived at business',
            26: 'Receiving',
            30: 'Picked up',
            35: 'Delivering',
            36: 'En route to warehouse',
            40: 'Arrived at customer',
            45: 'Delivered',
            50: 'Canceled',
            55: 'Failed',
            80: 'Pickup Failed',
            95: 'Terminated'
        }[code]

    @api.model
    def get_city_code(self, city):
        cities = {
            'C': 'EG-01',
            'GZ': 'EG-01',
            'SU': 'EG-01',
            'ALX': 'EG-02',
            'NCO': 'EG-03',
            'BH': 'EG-04',
            'DK': 'EG-05',
            'KB': 'EG-06',
            'GH': 'EG-07',
            'KFS': 'EG-08',
            'MNF': 'EG-09',
            'SHR': 'EG-10',
            'IS': 'EG-11',
            'SUZ': 'EG-12',
            'PTS': 'EG-13',
            'DT': 'EG-14',
            'FYM': 'EG-15',
            'BNS': 'EG-16',
            'AST': 'EG-17',
            'SHG': 'EG-18',
            'MN': 'EG-19',
            'KN': 'EG-20',
            'ASN': 'EG-21',
            'LX': 'EG-22'
        }
        code = cities.get(city, None)
        return code

    def bosta_cancel_shipment(self, pickings):
        pickings.write(
            {'carrier_tracking_ref': '', 'tracking_status': 'Canceled'
             })

    def bosta_get_tracking_link(self, pick):
        track_url = "https://bosta.co/tracking-shipments?shipment-number=" + pick.carrier_tracking_ref
        return track_url

