# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import base64

import codecs
import pprint

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch,cm,mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4, inch, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import simpleSplit
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER, TA_LEFT, TA_RIGHT
from cgi import escape
import time

class AccountMove(models.Model):
	_inherit = 'account.move'

	def generate_excel_rep_it(self):
		import io
		from xlsxwriter.workbook import Workbook

		ReportBase = self.env['report.base']
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Voucher.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("VOUCHER")
		worksheet.set_tab_color('blue')

		worksheet.write(0,0, "Libro:", formats['especial2'])
		worksheet.write(1,0, "Asiento:", formats['especial2'])
		worksheet.write(2,0, "Fecha Contable:", formats['especial2'])
		worksheet.write(3,0, "Fecha Documento:", formats['especial2'])
		worksheet.write(4,0, u"Compañía:", formats['especial2'])

		worksheet.write(0,3, "Para Revisar:", formats['especial2'])
		worksheet.write(1,3, u"Apertura/Cierre:", formats['especial2'])
		worksheet.write(2,3, "Medio de Pago:", formats['especial2'])
		worksheet.write(3,3, "Estado PLE:", formats['especial2'])
		worksheet.write(4,3, u"Fecha Correc PLE:", formats['especial2'])

		worksheet.write(0,1, self.journal_id.name, formats['especial4'])
		worksheet.write(1,1, self.name, formats['especial4'])
		worksheet.write(2,1, self.date , formats['especialdate'])
		worksheet.write(3,1, self.invoice_date if self.invoice_date else '', formats['especialdate'])
		worksheet.write(4,1, self.company_id.name, formats['especial4'])

		worksheet.write(0,4, 'True' if self.to_check else 'False', formats['especial4'])
		worksheet.write(1,4, 'True' if self.is_opening_close else 'False', formats['especial4'])
		worksheet.write(2,4, self.td_payment_id.description if self.td_payment_id else '' , formats['especial4'])
		worksheet.write(3,4, dict(self._fields['ple_state'].selection).get(self.ple_state) if self.ple_state else '', formats['especial4'])
		worksheet.write(4,4, self.date_corre_ple if self.date_corre_ple else '', formats['especialdate'])

		HEADERS = ['DESCRIPCION','CUENTA','SOCIO','TD','NRO','DEBE','HABER','MONTO IMP','TC']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,7,0,formats['boldbord'])

		x=8

		debit, credit = 0, 0

		for line in self.line_ids:
			worksheet.write(x,0,line.name if line.name else '',formats['especial1'])
			worksheet.write(x,1,line.account_id.name if line.account_id else '',formats['especial1'])
			worksheet.write(x,2,line.partner_id.name if line.partner_id else '',formats['especial1'])
			worksheet.write(x,3,line.type_document_id.code if line.type_document_id else '',formats['especial1'])
			worksheet.write(x,4,line.nro_comp if line.nro_comp else '',formats['especial1'])
			worksheet.write(x,5,line.debit if line.debit else '0.00',formats['numberdos'])
			worksheet.write(x,6,line.credit if line.credit else '0.00',formats['numberdos'])
			worksheet.write(x,7,line.tax_amount_it if line.tax_amount_it else '0.00',formats['numberdos'])
			worksheet.write(x,8,line.tc if line.tc else '1.00',formats['numbercuatro'])

			debit += line.debit if line.debit else 0
			credit += line.credit if line.credit else 0

			x += 1

		worksheet.write(x,5,debit,formats['numbertotal'])
		worksheet.write(x,6,credit,formats['numbertotal'])

		widths = [28,28,25,15,12,10,10,8,5]
		worksheet = ReportBase.resize_cells(worksheet,widths)

		##########################################AHORA OBTENDREMOS LOS DESTINOS############################################

		sql = """
			CREATE OR REPLACE view account_des_move as (SELECT row_number() OVER () AS id, * from vst_destinos where am_id = %s)""" % (
				str(self.id)
			)

		self.env.cr.execute(sql)

		self.env.cr.execute("SELECT * FROM account_des_move")
		res = self.env.cr.dictfetchall()

		if len(res) > 0:
			worksheet_destino = workbook.add_worksheet("DESTINOS")
			worksheet_destino.set_tab_color('blue')

			HEADERS_DES = ['PERIODO','FECHA','LIBRO','VOUCHER','CUENTA','DEBE','HABER','BALANCE','CTA ANALIT','DEST DEBE','DEST HABER']
			worksheet_destino = ReportBase.get_headers(worksheet_destino,HEADERS_DES,0,0,formats['boldbord'])

			x_des = 1

			for line in res:
				worksheet_destino.write(x_des,0,line['periodo'] if line['periodo'] else '',formats['especial1'])
				worksheet_destino.write(x_des,1,line['fecha'] if line['fecha'] else '',formats['dateformat'])
				worksheet_destino.write(x_des,2,line['libro'] if line['libro'] else '',formats['especial1'])
				worksheet_destino.write(x_des,3,line['voucher'] if line['voucher'] else '',formats['especial1'])
				worksheet_destino.write(x_des,4,line['cuenta'] if line['cuenta'] else '',formats['especial1'])
				worksheet_destino.write(x_des,5,line['debe'] if line['debe'] else '0.00',formats['numberdos'])
				worksheet_destino.write(x_des,6,line['haber'] if line['haber'] else '0.00',formats['numberdos'])
				worksheet_destino.write(x_des,7,line['balance'] if line['balance'] else '0.00',formats['numberdos'])
				worksheet_destino.write(x_des,8,line['cta_analitica'] if line['cta_analitica'] else '',formats['especial1'])
				worksheet_destino.write(x_des,9,line['des_debe'] if line['des_debe'] else '',formats['especial1'])
				worksheet_destino.write(x_des,10,line['des_haber'] if line['des_haber'] else '',formats['especial1'])
				x_des += 1

			widths_des = [12,8,8,10,10,10,10,10,10,10,10]
			worksheet_destino = ReportBase.resize_cells(worksheet_destino,widths_des)

		#####################################################################################################################
		
		workbook.close()

		f = open(direccion +'Voucher.xlsx', 'rb')

		return self.env['popup.it'].get_file('Voucher.xlsx',base64.encodestring(b''.join(f.readlines())))


	def generate_pdf_rep_it(self):
		#CREANDO ARCHIVO PDF
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')
		
		name_file = "Asiento_Contable.pdf"
	
		archivo_pdf = SimpleDocTemplate(str(direccion)+name_file, pagesize=letter, rightMargin=60,leftMargin=60, topMargin=30,bottomMargin=18)

		elements = []

		#PRIMERA DIVISION
		para_revisar = 'True' if self.to_check else 'False'
		ap_ci = 'True' if self.is_opening_close else 'False'
		med_pag = self.td_payment_id.description if self.td_payment_id else ''
		est_ple = dict(self._fields['ple_state'].selection).get(self.ple_state) if self.ple_state else ''
		fec_corr_ple = self.date_corre_ple if self.date_corre_ple else ''

		data = [['Libro:',(self.journal_id.name),'Para Revisar:',para_revisar],
				['Asiento:',(self.name),u'Apertura/Cierre:',ap_ci],
				['Fecha Contable:',self.date,'Medio de Pago:',med_pag],
				['Fecha Documento:',self.invoice_date,'Estado PLE:',est_ple],
				[u'Compañía:',self.company_id.name,'Fecha Correc PLE:',fec_corr_ple],[],[]]

		table_cab = Table(data, colWidths=[4*cm, 5*cm, 4*cm, 5*cm])

		elements.append(table_cab)

		#SEGUNDA DIVISION

		style_left = ParagraphStyle(name = 'Left', alignment=TA_LEFT, fontSize=9, fontName="Helvetica")
		style_right = ParagraphStyle(name = 'Right', alignment=TA_RIGHT, fontSize=9, fontName="Helvetica")
		style_title = ParagraphStyle(name = 'Center',alignment = TA_CENTER, fontSize = 10, fontName="Helvetica-Bold" )

		headers = [u'DESCRIPCIÓN','CUENTA','SOCIO','TD','NRO','DEBE','HABER','MONTO IMP','TC']

		datos = []

		datos.append([])

		for i in headers:
			datos[0].append(Paragraph(i,style_title))
		
		debit, credit = 0,0

		for c,line in enumerate(self.line_ids):
			datos.append([])
			datos[c+1].append(Paragraph(line.name if line.name else '',style_left))
			datos[c+1].append(Paragraph(line.account_id.name if line.account_id else '',style_left))
			datos[c+1].append(Paragraph(line.partner_id.name if line.partner_id else '',style_left))
			datos[c+1].append(Paragraph(line.type_document_id.code if line.type_document_id else '',style_left))
			datos[c+1].append(Paragraph(line.nro_comp if line.nro_comp else '',style_left))
			datos[c+1].append(Paragraph(str(line.debit) if line.debit else '0.00',style_right))
			datos[c+1].append(Paragraph(str(line.credit) if line.credit else '0.00',style_right))
			datos[c+1].append(Paragraph(str(line.tax_amount_it) if line.tax_amount_it else '0.00',style_right))
			datos[c+1].append(Paragraph(str(line.tc) if line.tc else '1.0000',style_right))

			debit += line.debit if line.debit else 0
			credit += line.credit if line.credit else 0

		datos.append(['','','','','Total:',str(debit),str(credit),'',''])

		table_datos = Table(datos, colWidths=[3*cm, 3*cm, 4*cm, 1*cm,1.5*cm,1.8*cm,1.8*cm,1.9*cm,1*cm])

		color_cab = colors.Color(red=(220/255),green=(230/255),blue=(241/255))

		style_table = TableStyle([
				('BACKGROUND', (0, 0), (10, 0),color_cab),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('GRID', (0,0), (-1,-1), 0.25, colors.black), 
				('BOX', (0,0), (-1,-1), 0.25, colors.black),
			])
		table_datos.setStyle(style_table)

		elements.append(table_datos)

		##TERCERA DIVISION - DESTINOS

		sql = """
			CREATE OR REPLACE view account_des_move as (SELECT row_number() OVER () AS id, * from vst_destinos where am_id = %s)""" % (
				str(self.id)
			)

		self.env.cr.execute(sql)

		self.env.cr.execute("SELECT * FROM account_des_move")
		res = self.env.cr.dictfetchall()

		if len(res) > 0:

			elements.append(Spacer(1, 30))
			style_left = ParagraphStyle(name = 'Left', alignment=TA_LEFT, fontSize = 8, fontName="Helvetica")
			style_right = ParagraphStyle(name = 'Right', alignment=TA_RIGHT, fontSize = 8, fontName="Helvetica")
			style_title = ParagraphStyle(name = 'Center',alignment = TA_CENTER, fontSize = 9, fontName="Helvetica-Bold" )

			headers = ['PERIODO','FECHA','LIBRO','VOUCHER','CUENTA','DEBE','HABER','BALANCE','CTA ANALIT','DEST DEBE','DEST HABER']

			datos2 = []

			datos2.append([])

			for i in headers:
				datos2[0].append(Paragraph(i,style_title))

			for c,line in enumerate(res):
				datos2.append([])
				datos2[c+1].append(Paragraph(line['periodo'] if line['periodo'] else '',style_left))
				datos2[c+1].append(Paragraph(line['fecha'] if line['fecha'] else '',style_left))
				datos2[c+1].append(Paragraph(line['libro'] if line['libro'] else '',style_left))
				datos2[c+1].append(Paragraph(line['voucher'] if line['voucher'] else '',style_left))
				datos2[c+1].append(Paragraph(line['cuenta'] if line['cuenta'] else '',style_left))
				datos2[c+1].append(Paragraph(str(line['debe']) if line['debe'] else '0.00',style_right))
				datos2[c+1].append(Paragraph(str(line['haber']) if line['haber'] else '0.00',style_right))
				datos2[c+1].append(Paragraph(str(line['balance']) if line['balance'] else '0.00',style_right))
				datos2[c+1].append(Paragraph(line['cta_analitica'] if line['cta_analitica'] else '',style_left))
				datos2[c+1].append(Paragraph(line['des_debe'] if line['des_debe'] else '',style_left))
				datos2[c+1].append(Paragraph(line['des_haber'] if line['des_haber'] else '',style_left))

			table_datos_2 = Table(datos2, colWidths=[1.9*cm, 1.85*cm, 1.6*cm, 2.1*cm,1.8*cm,1.6*cm,1.6*cm,1.99*cm,2*cm,1.6*cm,1.6*cm])

			table_datos_2.setStyle(style_table)

			elements.append(table_datos_2)
		
		#Build
		archivo_pdf.build(elements)

		#Caracteres Especiales
		import importlib
		import sys
		importlib.reload(sys)
		import os


		f = open(str(direccion) + name_file, 'rb')		

		return self.env['popup.it'].get_file(name_file,base64.encodestring(b''.join(f.readlines())))


