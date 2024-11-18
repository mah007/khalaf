from odoo import models, fields, api

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
    ], string='Status', compute='_compute_status', store=True)
    total_cash = fields.Float(string="Total Cash Collection", compute='_compute_total_collection')
    total_visa = fields.Float(string="Total Visa Collection", compute='_compute_total_collection')
    total_amount = fields.Float(string="Total Amount", compute='_compute_total_collection')

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
            cash_total = sum(order.amount_total for order in record.delivery_order_ids if order.payment_method == 'cash')
            visa_total = sum(order.amount_total for order in record.delivery_order_ids if order.payment_method == 'visa')
            record.total_cash = cash_total
            record.total_visa = visa_total
            record.total_amount = cash_total + visa_total

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    delivery_boy_id = fields.Many2one('stock.delivery.boy', string='Delivery Boy')
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('visa', 'Visa')
    ], string="Payment Method", help="Indicates if payment was made by cash or visa.")

class AssignDeliveryBoyWizard(models.TransientModel):
    _name = 'assign.delivery.boy.wizard'
    _description = 'Assign Delivery Boy Wizard'

    delivery_boy_id = fields.Many2one('stock.delivery.boy', string="Delivery Boy", required=True)
    order_ids = fields.Many2many('stock.picking', string="Orders")

    def action_assign_delivery_boy(self):
        for order in self.order_ids:
            order.delivery_boy_id = self.delivery_boy_id
