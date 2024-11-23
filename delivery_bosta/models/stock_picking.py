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
import datetime
from dateutil.relativedelta import relativedelta

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
import json
import requests
import logging

_logger = logging.getLogger('BOSTA STATUS UPDATE ====>')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    bosta_delivery_id = fields.Char(string="Bosta Delivery Number")
    bosta_awb = fields.Binary(string="Bosta AWB", readonly=True,
                              attachment=True, copy=False)
    bosta_awb_filename = fields.Char(string="Bosta AWB File Name",
                                     required=False)
    tracking_status = fields.Char(string="Tracking Status", copy=False)

    def bosta_set_delivered(self):
        self.tracking_status = 'Delivered'

    def bosta_set_returned(self):
        self.tracking_status = 'Returned to Shipper'

    def bosta_set_cancelled(self):
        self.tracking_status = 'Order Cancelled'

    def _action_done(self):
        return super(StockPicking,
                     self.with_context(skip_bosta_shipper=True))._action_done()

    @api.model
    def cron_bosta_update_tracking(self):
        status_list = self.env['bosta.status'].search([]).mapped('name')
        start_date = datetime.datetime.now() + relativedelta(months=-1)
        records = self.env['stock.picking'].sudo().search(
            [('delivery_type', '=', 'bosta'),
             ('state', '=', 'done'),
             ('create_date', '>', start_date),
             ('tracking_status', 'not in', status_list)], order='date desc')
        i = len(records)
        for i, record in enumerate(records):
            status = record.carrier_id.bosta_get_status(
                record.bosta_delivery_id) or record.tracking_status
            _logger.info(
                '%s-%s -- Updating Picking : %s has old status : %s  with status : %s' % (
                    i, len(records),
                    record.name, record.tracking_status, status))
            record.write({
                'tracking_status': status
            })

    def update_bosta_tracking_status(self):
        for i, record in enumerate(self):
            if not record.carrier_id or record.carrier_id.delivery_type != 'bosta' or record.state != 'done':
                continue
            status = record.carrier_id.bosta_get_status(
                record.bosta_delivery_id) or record.tracking_status
            _logger.info(
                '%s-%s -- Updating Picking : %s has old status : %s  with status : %s' % (
                    i, len(self),
                    record.name, record.tracking_status, status))
            record.write({
                'tracking_status': status
            })

    def send_to_shipper(self):
        self.ensure_one()
        pickings = self
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        context["active_model"] = "stock.picking"
        if pickings.carrier_id.delivery_type != 'bosta':
            return super(StockPicking, self).send_to_shipper()
        elif pickings.carrier_id.delivery_type == 'bosta' and context.get(
                'skip_bosta_shipper', False):
            return True

        if pickings and pickings.carrier_id.delivery_type == "bosta" and 'vals_for_shipping' not in context:
            warehouse_partner = pickings.picking_type_id.warehouse_id.partner_id
            if not warehouse_partner:
                raise ValidationError(_('Please Set Address To Sale Warehouse'))
            customer = pickings.partner_id
            delivery_note = self.bosta_get_delivery_note()
            receiver_vals = self.bosta_get_receiver_vals()
            pickup_vals = self.bosta_get_pickup_vals()
            cod_amount = pickings.get_cod_amount()
            pickup_city = pickings.carrier_id.get_city_code(
                warehouse_partner.state_id.code)
            if not pickup_city:
                raise ValidationError(_(
                    "Please configure your warehouse address " % warehouse_partner.state_id.name))

            dropoff_city = pickings.carrier_id.get_city_code(
                customer.state_id.code)

            if not dropoff_city:
                raise UserError(
                    "Bosta doesnt not ship to/from " + customer.state_id.name)
            if pickings.carrier_id.bosta_shipment_type == 'crp':
                cod_amount = -cod_amount

            vals = {**pickup_vals, **receiver_vals,

                    "cod_amount": cod_amount,
                    "businessReference": pickings.sale_id.name,
                    "notes": delivery_note,

                    "picking_id": pickings.id,
                    }

            # view = self.env['ir.model.data'].xmlid_to_res_id(
            #     'delivery_bosta.bosta_wizard_form')
            # view = self.sudo().env.ref('delivery_bosta.bosta_wizard_form')
            # view_id = self.env.ref('delivery_bosta.bosta_wizard_form').id
            wiz_id = self.env['bosta.wizard'].create(vals)
            action = self.env["ir.actions.actions"]._for_xml_id('delivery_bosta.bosta_wizard_view_action')
            action.update({
                'res_id': wiz_id.id,
                'target': 'new',
                'name': _('Bosta Shipment'),
            })
            return action
        res = self.carrier_id.send_shipping(self[0])
        self.carrier_tracking_ref = res['tracking_number']
        if self.sale_id:
            self.write({
                'carrier_tracking_ref': res['tracking_number']
            })
        self.bosta_delivery_id = res['delivery_id']
        self.tracking_status = res['status']
        bosta_awb = self.carrier_id.bosta_get_awb(self.bosta_delivery_id)
        self.write({'bosta_awb': bosta_awb,
                    'bosta_awb_filename': 'AWB_{}.pdf'.format(
                        self.bosta_delivery_id)})

        msg = _('Shipment sent to  carrier %s for expedition with '
                'tracking number %s and delivery Id %s') % (
                  self.carrier_id.name, self.carrier_tracking_ref,
                  self.bosta_delivery_id)

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        msg = _(
            '<br/>Please Download the AWB pdf From The Following URL : '
            '<a target="_blank" href="{}/bosta/download/{}">{}</a>'.format(
                base_url, self.bosta_delivery_id, self.bosta_awb_filename
            )
        )
        self.message_post(body=msg, subtype_xmlid="mail.mt_comment")

    def bosta_get_receiver_vals(self):
        self.ensure_one()
        customer = self.partner_id
        email = customer.email
        if not email and customer.parent_id:
            email = customer.parent_id.email
        customer_name = customer.name and customer.name.split()
        dropoff_city = self.carrier_id.get_city_code(
            customer.state_id.code)

        if not dropoff_city:
            raise UserError(
                "Bosta doesnt not ship to " + customer.state_id.name)

        zone = customer.city
        if not zone and hasattr(customer, 'city_id'):
            zone = customer.city_id.name
        receiver_vals = {
            "receiver_firstname": customer_name[0],
            "receiver_lastname": customer_name[len(customer_name) - 1],
            "receiver_phone": customer.mobile or customer.phone or '',
            "receiver_email": email,
            "receiver_street1": customer.street or '',
            "receiver_street2": customer.street2 or '',
            "receiver_zone": zone or '',
            "receiver_city": customer.state_id.id,
            "receiver_city_code": dropoff_city,

        }
        if self.carrier_id.bosta_shipment_type == 'crp':
            warehouse_partner = self.picking_type_id.warehouse_id.partner_id
            dropoff_city = self.carrier_id.get_city_code(
                warehouse_partner.state_id.code)
            if not dropoff_city:
                raise ValidationError(_(
                    "Please configure your warehouse address " % warehouse_partner.state_id.name))

            zone = warehouse_partner.city
            if not zone and hasattr(customer, 'city_id'):
                zone = warehouse_partner.city_id.name
            receiver_vals.update({
                "receiver_firstname": customer_name[0],
                "receiver_lastname": customer_name[len(customer_name) - 1],
                "receiver_phone": customer.mobile or customer.phone or '',
                "receiver_email": email,
                "receiver_street1": warehouse_partner.street or '',
                "receiver_street2": warehouse_partner.street2 or '',
                "receiver_zone": zone or '',
                "receiver_city": warehouse_partner.state_id.id,
                "receiver_city_code": dropoff_city,

            })
        return receiver_vals

    def bosta_get_pickup_vals(self):
        self.ensure_one()
        warehouse_partner = self.picking_type_id.warehouse_id.partner_id
        pickup_city = self.carrier_id.get_city_code(
            warehouse_partner.state_id.code)
        if not pickup_city:
            raise ValidationError(_(
                "Please configure your warehouse address " % warehouse_partner.state_id.name))
        pickup_vals = {
            # Pickup Address
            "pickup_street1": warehouse_partner.street,
            "pickup_street2": warehouse_partner.street2,
            "pickup_zone": warehouse_partner.city,
            "pickup_city": warehouse_partner.state_id.id,
            "pickup_city_code": pickup_city,
        }
        if self.carrier_id.bosta_shipment_type == 'crp':
            customer = self.partner_id
            email = customer.email
            if not email and customer.parent_id:
                email = customer.parent_id.email
            customer_name = customer.name.split()
            pickup_city = self.carrier_id.get_city_code(
                customer.state_id.code)

            if not pickup_city:
                raise UserError(
                    "Bosta doesnt not ship to " + customer.state_id.name)
            pickup_vals = {
                # Pickup Address
                "pickup_street1": customer.street,
                "pickup_street2": customer.street2,
                "pickup_zone": customer.city,
                "pickup_city": customer.state_id.id,
                "pickup_city_code": pickup_city,
            }

        return pickup_vals

    def bosta_get_delivery_note(self):
        self.ensure_one()
        delivery_note = ''
        product_desc = []
        for ml in self.move_ids:
            if ml.quantity <= 0:
                continue
            line_description = '[{}]{}-({})\n'.format(
                ml.product_id.default_code,
                ml.product_id.name,
                ml.product_uom_qty)
            product_desc.append(line_description)
        products_description = '+++'.join(product_desc)

        delivery_note += products_description

        if self.carrier_id.bosta_delivery_note:
            delivery_note += '+++' + self.carrier_id.bosta_delivery_note
        return delivery_note

    def get_cod_amount(self):
        self.ensure_one()
        amount = 0
        if self.sale_id:
            amount = self.sale_id.amount_total
        return amount
