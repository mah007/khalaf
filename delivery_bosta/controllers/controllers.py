# -*- coding: utf-8 -*-

##############################################################################
#
#
#    Copyright (C) 2019-TODAY .
#    Author: Eng.Ramadan Khalil (<rkhalil1990@gmail.com>)
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
##############################################################################


from odoo import http
import base64
import io
import werkzeug
from reportlab.pdfgen import canvas
from PyPDF2 import PdfFileReader, PdfFileWriter


class BostaDeliveryCarrier(http.Controller):

    @http.route('/bosta/download/<id>', auth='user', type='http')
    def download_awb(self,id):
        picking = http.request.env['stock.picking'].sudo().search([('bosta_delivery_id','=',id)])

        pdf = picking.carrier_id.bosta_get_awb(picking.bosta_delivery_id)
        file=io.BytesIO(base64.b64decode(pdf))
        bosta_pdf = PdfFileReader(file,
                                  strict=False, overwriteWarnings=False)
        new_pdf = PdfFileWriter()
        for p in range(0, bosta_pdf.getNumPages()):
            page = bosta_pdf.getPage(p)
            page.rotateClockwise(270)

            page.mediaBox.lowerLeft = (page.mediaBox.getLowerLeft_x(),
                                       page.mediaBox.getLowerLeft_y() + 285)



            new_pdf.addPage(page)

        packet = io.BytesIO()
        can = canvas.Canvas(packet)

        output = io.BytesIO()
        new_pdf.write(output)

        response = werkzeug.wrappers.Response()
        response.data = output.getvalue()
        response.mimetype = 'application/pdf'
        return response
        # if pdf:
        #     # return pdf
        #     response = werkzeug.wrappers.Response()
        #     response.data = file.getvalue()
        #     response.mimetype = 'application/pdf'
        #     return response
        # else:
        #     return http.Response(status=503)