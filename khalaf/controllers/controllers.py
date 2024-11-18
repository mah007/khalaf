# -*- coding: utf-8 -*-
# from odoo import http


# class Khalaf(http.Controller):
#     @http.route('/khalaf/khalaf', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/khalaf/khalaf/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('khalaf.listing', {
#             'root': '/khalaf/khalaf',
#             'objects': http.request.env['khalaf.khalaf'].search([]),
#         })

#     @http.route('/khalaf/khalaf/objects/<model("khalaf.khalaf"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('khalaf.object', {
#             'object': obj
#         })

