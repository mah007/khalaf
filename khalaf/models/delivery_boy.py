from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    delivery_boy = fields.Boolean(string="Is Delivery Boy", default=False)


class StockDeliveryBoy(models.Model):
    _name = 'stock.delivery.boy'
    _description = 'Stock Delivery Boy Assignment'

    name = fields.Char(string='Name', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    delivery_order_ids = fields.One2many('stock.picking', 'delivery_boy_id', string='Delivery Orders')
    assigned_date = fields.Datetime(string='Assigned Date', default=fields.Datetime.now)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ], string='Status', default='pending', store=True)
    total_cash = fields.Float(string="Total Cash Collection", compute='_compute_total_collection')
    total_visa = fields.Float(string="Total Visa Collection", compute='_compute_total_collection')
    total_insta = fields.Float(string="Total InstaPay Collection", compute='_compute_total_collection')
    total_voda = fields.Float(string="Total Vodafone Collection", compute='_compute_total_collection')
    total_amount = fields.Float(string="Total Amount", compute='_compute_total_collection')

    def done_collection(self):
        for rec in self:
            for order in rec.delivery_order_ids:
                if order.sale_id:
                    order.sale_id.collection_status = 'collected'
                    order.button_validate()

    def action_process(self):
        for rec in self:
            rec.status = 'in_progress'

    def action_done(self):
        for rec in self:
            rec.status = 'completed'
            rec.done_collection()

    @api.depends('delivery_order_ids.state')
    def _compute_status(self):
        for record in self:
            if all(order.state == 'done' for order in record.delivery_order_ids):
                record.status = 'completed'
            elif any(order.state == 'in_progress' for order in record.delivery_order_ids):
                record.status = 'in_progress'
            else:
                record.status = 'pending'

    @api.depends('delivery_order_ids')
    def _compute_total_collection(self):
        for record in self:
            cash_total = sum(order.sale_id.amount_total for order in record.delivery_order_ids if order.payment_method == 'cash')
            visa_total = sum(order.sale_id.amount_total for order in record.delivery_order_ids if order.payment_method == 'visa')
            insta_total = sum(order.sale_id.amount_total for order in record.delivery_order_ids if order.payment_method == 'insta')
            voda_total = sum(order.sale_id.amount_total for order in record.delivery_order_ids if order.payment_method == 'voda')
            record.total_cash = cash_total
            record.total_visa = visa_total
            record.total_insta = insta_total
            record.total_voda = voda_total
            record.total_amount = cash_total + visa_total + insta_total + voda_total


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    delivery_boy_id = fields.Many2one('stock.delivery.boy', string='Delivery Boy')
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('insta', 'InstaPay'),
        ('voda', 'Vodafone'),
        ('visa', 'Visa')
    ], string="Payment Method", help="Indicates if payment was made by cash or visa.", compute='_compute_payment_method')
    partner_shipping_id = fields.Many2one(
        comodel_name='res.partner',
        string="Delivery Address info",
        compute='_compute_partner_shipping_id',
        store=True, readonly=False, required=True, precompute=True,
        check_company=True,
        index='btree_not_null')
    assigning = fields.Selection([('assigned', 'Assigned'), ('not_assigned', 'Not Assigned')], default='not_assigned', string="Is Assigned", compute='_compute_assigning', store=True)

    @api.depends('partner_id')
    def _compute_partner_shipping_id(self):
        for order in self:
            order.partner_shipping_id = order.partner_id.address_get(['delivery'])['delivery'] if order.partner_id else False

    @api.depends('partner_id')
    def _compute_assigning(self):
        for order in self:
            order.assigning = 'assigned' if order.delivery_boy_id else 'not_assigned'

    # @api.depends('sale_id')
    def _compute_payment_method(self):
        for order in self:
            if order.sale_id:
                order.payment_method = order.sale_id.payment_method
            else:
                order.payment_method = 'cash'


class AssignDeliveryBoyWizard(models.TransientModel):
    _name = 'assign.delivery.boy.wizard'
    _description = 'Assign Delivery Boy Wizard'

    delivery_boy_id = fields.Many2one(
        'hr.employee',
        string="Delivery Boy",
        domain="[('delivery_boy', '=', True)]",  # Only employees with the delivery boy option set to True
        required=True
    )
    order_ids = fields.Many2many(
        'stock.picking',
        string="Orders",
        default=lambda self: self._default_orders()
    )

    @api.model
    def _default_orders(self):
        """Get default orders from the context's active_ids."""
        active_ids = self.env.context.get('active_ids', [])
        return self.env['stock.picking'].browse(active_ids)

    def action_assign_delivery_boy(self):
        """Assign the selected delivery boy to the selected orders and create a single stock.delivery.boy record."""
        # Create a new record in stock.delivery.boy for all selected orders
        delivery_boy_record = self.env['stock.delivery.boy'].create({
            'name': f"{self.delivery_boy_id.name} - {datetime.now().strftime('%Y-%m-%d %I:%M %p')}",
            'employee_id': self.delivery_boy_id.id,
            'delivery_order_ids': [(6, 0, self.order_ids.ids)],
            'assigned_date': fields.Datetime.now(),
            'status': 'in_progress',  # Default to in_progress status
        })

        # Assign the delivery boy record to each order
        for order in self.order_ids:
            order.delivery_boy_id = delivery_boy_record.id
            # order.button_validate()


