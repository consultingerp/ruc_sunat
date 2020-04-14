# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError
import base64

import codecs
import pprint

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch,cm,mm
from reportlab.lib.colors import magenta, red , black , blue, gray, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4, inch, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import simpleSplit
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER,TA_LEFT,TA_RIGHT
from cgi import escape
import time

class AccountJournalRep(models.TransientModel):
	_name = 'account.journal.rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=1)
	exercise = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	date_ini = fields.Date(string=u'Fecha Inicial',required=True)
	date_end = fields.Date(string=u'Fecha Final',required=True)
	type_show = fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('pdf','PDF'),('csv','CSV')],string=u'Mostrar en',default='pantalla', required=True)
	libros = fields.Many2many('account.journal','account_book_journal_rel','id_book_origen','id_journal_destino',string=u'Libros', required=True)

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			fiscal_year = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).fiscal_year
			if fiscal_year:
				self.exercise = fiscal_year.id
				self.date_ini = fiscal_year.date_from
				self.date_end = fiscal_year.date_to
			else:
				raise UserError(u'No existe un año Fiscal configurado en Parametros Principales de Contabilidad para esta Compañía')

	def _get_sql(self,content):
		sql_journals = ""
		libros_ids = self.libros.ids

		#Solo algunos libros
		if content == 1:
			sql_journals = "and journal_id in (%s) " % (','.join(str(i) for i in libros_ids))

		sql = """select id,
			periodo,fecha,libro,voucher,
			cuenta,debe,haber,balance,
			moneda,tc,importe_me,code_cta_analitica,
			glosa,td_partner,doc_partner,partner,
			td_sunat,nro_comprobante,fecha_doc,fecha_ven,
			col_reg,monto_reg,medio_pago,ple_diario,
			ple_compras,ple_ventas,registro
			from vst_diariog
			where (fecha between '%s' and '%s')
			and company_id = %s %s
		""" % (self.date_ini.strftime('%Y/%m/%d'),
			self.date_end.strftime('%Y/%m/%d'),
			str(self.company_id.id),
			sql_journals)
		return sql

	def get_all(self):

		#filtro = []	
		self.env.cr.execute("""
			CREATE OR REPLACE view account_journal_book as ("""+self._get_sql(0)+""")""")
			
		if self.type_show == 'pantalla':
			return {
				'name': 'Libro Diario',
				'type': 'ir.actions.act_window',
				'res_model': 'account.journal.book',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}

		if self.type_show == 'excel':
			return self.get_excel()
		
		if self.type_show == 'pdf':
			return self.getPdf()
		
		if self.type_show == 'csv':
			return self.getCsv()

	def get_ple_diario(self):
		return self.get_ples(1)

	def get_ple_mayor(self):
		return self.get_ples(2)

	def get_ple_plan_contable(self):
		return self.get_ples(3)

	def get_ples(self,type):
		#1 -> PLE Diario
		#2 -> PLE Mayor
		#3 -> PLE Plan Contable

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_ple_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio PLE configurado en Parametros Principales de Contabilidad para su Compañía')

		ruc = self.company_id.partner_id.vat
		mond = self.company_id.currency_id.name

		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		if not mond:
			raise UserError('No configuro la moneda de su Compañia.')

		#LE + RUC + AÑO(YYYY) + MES(MM) + DIA(00) + IDENTIFICADOR DEL LIBRO
		name_doc = "LE"+str(ruc)+str(self.date_ini.year)+str('{:02d}'.format(self.date_ini.month))+"00"

		#Get CSV
		sql_query = """	COPY ("""+self._get_sql_ple(type,self.date_ini,self.date_end,self.company_id.id)+""")TO '"""+direccion+"""ple.csv' WITH DELIMITER '|' """
		self.env.cr.execute(sql_query)

		#NOMENCLATURA
		if type == 1:
			name_doc += "050100"
		if type == 2:
			name_doc += "060100"
		if type == 3:
			name_doc += "050300"

		#Caracteres Especiales
		import importlib
		import sys
		importlib.reload(sys)

		exp = ''.join(open(str(direccion + 'ple.csv'),'r').readlines())
		# CODIGO DE OPORTUNIDAD DE PRESENTACION DEL EEFF (00) +
		# INDICADOR DE OPERACIONES (1) +
		# INDICADOR DE CONTENIDO Con informacion(1), Sin informacion(0) +
		# INDICADOR DE MONEDA UTILIZADA Nuevos Soles(1), US Dolares(2) +
		# INDICADOR DE LIBRO ELECTRONICO GENERADO POR EL PLE (1)

		name_doc += "00"+"1"+("1" if len(exp) > 0 else "0") + ("1" if mond == 'PEN' else "2") + "1.txt"

		return self.env['popup.it'].get_file(name_doc,base64.encodestring(b''.join(open(str(direccion + 'ple.csv'),'rb').readlines()) if exp else b"== Sin Registros =="))	

	def _get_sql_ple(self,type,x_date_ini,x_date_end,x_company_id):
		#1 -> PLE Diario
		#2 -> PLE Mayor
		#3 -> PLE Plan Contable
		sql_order_by_periodo_cuenta = ""

		if type == 1 or type == 2:
			if type == 2:
				sql_order_by_periodo_cuenta = " ORDER BY vst_d.periodo, vst_d.cuenta"

			self.env.cr.execute("""select cuo from account_move_line where cuo is null and (date between '%s' and '%s')""" % (x_date_ini.strftime('%Y/%m/%d'),x_date_end.strftime('%Y/%m/%d')))
			res = self.env.cr.dictfetchall()

			if len(res) > 0:
				raise UserError("Debe generar primeros los CUOs en la fecha especificada. En la ruta Contabilidad/Informes/Libros Peruanos/Generar CUOs")

			sql = """SELECT 
					CASE
						WHEN right(vst_d.periodo,2) = '00' THEN left(vst_d.periodo,4) ||'0100'
						WHEN right(vst_d.periodo,2) = '13' THEN left(vst_d.periodo,4) ||'1200'
						ELSE vst_d.periodo || '00'
					END AS campo1,
					aml.cuo AS campo2,
					CASE
						WHEN right(vst_d.periodo,2) = '00' THEN 'A' || vst_d.voucher
						WHEN right(vst_d.periodo,2) = '13' THEN 'C' || vst_d.voucher
						ELSE 'M' || vst_d.voucher
					END AS campo3,
					vst_d.cuenta AS campo4,
					'' AS campo5,
					'' AS campo6,
					vst_d.moneda AS campo7,
					CASE
						WHEN vst_d.td_partner is not null THEN vst_d.td_partner
						ELSE '0'
					END AS campo8,
					CASE
						WHEN vst_d.doc_partner is not null THEN vst_d.doc_partner
						ELSE '0'
					END AS campo9,
					CASE
						WHEN vst_d.td_sunat is not null THEN vst_d.td_sunat
						ELSE '00'
					END AS campo10,
					CASE
						WHEN vst_d.nro_comprobante is not null and position('-' in vst_d.nro_comprobante::text) <> 0 THEN split_part(vst_d.nro_comprobante, '-', 1)
						ELSE ''
					END AS campo11,
					CASE
						WHEN vst_d.nro_comprobante is not null and position('-' in vst_d.nro_comprobante::text) <> 0 THEN split_part(vst_d.nro_comprobante, '-', 2)
						WHEN vst_d.nro_comprobante is not null and position('-' in vst_d.nro_comprobante::text) = 0 THEN split_part(vst_d.nro_comprobante, '-', 1)
						ELSE '0'
					END AS campo12,
					TO_CHAR(vst_d.fecha::DATE, 'dd/mm/yyyy') AS campo13,
					CASE
						WHEN vst_d.fecha_ven is not null THEN TO_CHAR(vst_d.fecha_ven::DATE, 'dd/mm/yyyy')
						ELSE ''
					END AS campo14,
					CASE
						WHEN vst_d.fecha_doc is not null THEN TO_CHAR(vst_d.fecha_doc::DATE, 'dd/mm/yyyy')
						ELSE TO_CHAR(vst_d.fecha::DATE, 'dd/mm/yyyy')
					END AS campo15,
					CASE
						WHEN aml.name <> '' THEN left(aml.name,200)
						ELSE '-'
					END AS campo16,
					'' AS campo17,
					vst_d.debe AS campo18,
					vst_d.haber AS campo19,
					CASE
						WHEN aj.register_sunat = '1' and rp.is_not_home = FALSE THEN '080100'|| '&' || vst_d.periodo || '&' || aml.cuo|| '&' || 'M' || vst_d.voucher
						WHEN aj.register_sunat = '1' and rp.is_not_home = TRUE THEN '080200'|| '&' || vst_d.periodo || '&' ||  aml.cuo|| '&' || 'M' || vst_d.voucher
						WHEN aj.register_sunat = '2' THEN '140100' || '&' || vst_d.periodo|| '&' ||  aml.cuo || '&' || 'M' || vst_d.voucher
						ELSE ''
					END AS campo20,
					am.ple_state AS campo21,
					'' AS campo22
					FROM vst_diariog vst_d
					LEFT JOIN account_move_line aml ON aml.id = vst_d.move_line_id
					LEFT JOIN account_move am ON am.id = vst_d.move_id
					LEFT JOIN account_journal aj ON aj.id = am.journal_id
					LEFT JOIN res_partner rp ON rp.id = vst_d.partner_id
					WHERE (vst_d.fecha between '%s' and '%s')
					and vst_d.company_id = %s
					and aml.cuo is not null
					%s
					""" % (x_date_ini.strftime('%Y/%m/%d'),
					x_date_end.strftime('%Y/%m/%d'),
					str(x_company_id),str(sql_order_by_periodo_cuenta))

		else:
			code_sunat = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).account_plan_code.code_sunat
			if not code_sunat:
				raise UserError(u"Debe configurar el Codigo Sunat el registro Codigo Plan de Cuentas ubicado en Parametros Principales/SUNAT de Contabilidad para su Compañía")

			sql = """
					SELECT
					to_char(ap.date_end,'yyyymmdd') AS campo1,
					T1.cuenta AS campo2,
					LEFT(aa.name,100) AS campo3,
					'%s' AS campo4,
					'' AS campo5,
					'' AS campo6,
					'' AS campo7,
					am.ple_state AS campo8,
					'' AS campo9
					FROM (
					SELECT cuenta, max(move_line_id) AS min_line_id
					FROM vst_diariog
					WHERE (fecha BETWEEN '%s' AND '%s')
					AND company_id = %s AND cuenta is not null
					GROUP BY cuenta)T1
					LEFT JOIN vst_diariog T2 ON T2.move_line_id = T1.min_line_id
					LEFT JOIN account_account aa ON aa.id = T2.account_id
					LEFT JOIN account_move am ON am.id = T2.move_id
					LEFT JOIN account_period ap ON ap.code = T2.periodo
					ORDER BY T2.periodo, T1.cuenta
					""" % (code_sunat,x_date_ini.strftime('%Y/%m/%d'),
					x_date_end.strftime('%Y/%m/%d'),
					str(x_company_id))

		return sql

	def get_journals(self):
		if self.libros:
			self.env.cr.execute("""
				CREATE OR REPLACE view account_journal_book as ("""+self._get_sql(1)+""")""")

			if self.type_show == 'pantalla':
				return {
					'name': 'Libro Diario',
					'type': 'ir.actions.act_window',
					'res_model': 'account.journal.book',
					'view_mode': 'tree',
					'view_type': 'form',
					'views': [(False, 'tree')],
				}
				
			if self.type_show == 'excel':
				return self.get_excel()
			
			if self.type_show == 'pdf':
				return self.getPdf()
			
			if self.type_show == 'csv':
				return self.getCsv()
		else:
			raise UserError('Debe escoger al menos un libro.')

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Libro_Diario.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########LIBRO DIARIO############
		worksheet = workbook.add_worksheet("LIBRO DIARIO")
		worksheet.set_tab_color('blue')

		HEADERS = ['PERIODO','FECHA','LIBRO','VOUCHER','CUENTA','DEBE','HABER','BALANCE','MON','TC','IMP ME',
		'CTA ANALITICA','GLOSA','TDP','RUC','PARTNER','TD','NRO COMP','FECHA DOC','FECHA VEN','COL REG','MONTO REG','MED PAGO',
		'PLE DIARIO','PLE COMPRAS','PLE VENTAS']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		for line in self.env['account.journal.book'].search([]):
			worksheet.write(x,0,line.periodo if line.periodo else '',formats['especial1'])
			worksheet.write(x,1,line.fecha if line.fecha else '',formats['dateformat'])
			worksheet.write(x,2,line.libro if line.libro else '',formats['especial1'])
			worksheet.write(x,3,line.voucher if line.voucher else '',formats['especial1'])
			worksheet.write(x,4,line.cuenta if line.cuenta else '',formats['especial1'])
			worksheet.write(x,5,line.debe if line.debe else '0.00',formats['numberdos'])
			worksheet.write(x,6,line.haber if line.haber else '0.00',formats['numberdos'])
			worksheet.write(x,7,line.balance if line.balance else '0.00',formats['numberdos'])
			worksheet.write(x,8,line.moneda if line.moneda else '',formats['especial1'])
			worksheet.write(x,9,line.tc if line.tc else '0.0000',formats['numbercuatro'])
			worksheet.write(x,10,line.importe_me if line.importe_me else '0.00',formats['numberdos'])
			worksheet.write(x,11,line.code_cta_analitica if line.code_cta_analitica else '',formats['especial1'])
			worksheet.write(x,12,line.glosa if line.glosa else '',formats['especial1'])
			worksheet.write(x,13,line.td_partner if line.td_partner else '',formats['especial1'])
			worksheet.write(x,14,line.doc_partner if line.doc_partner else '',formats['especial1'])
			worksheet.write(x,15,line.partner if line.partner else '',formats['especial1'])
			worksheet.write(x,16,line.td_sunat if line.td_sunat else '',formats['especial1'])
			worksheet.write(x,17,line.nro_comprobante if line.nro_comprobante else '',formats['especial1'])
			worksheet.write(x,18,line.fecha_doc if line.fecha_doc else '',formats['dateformat'])
			worksheet.write(x,19,line.fecha_ven if line.fecha_ven else '',formats['dateformat'])
			worksheet.write(x,20,line.col_reg if line.col_reg else '',formats['especial1'])
			worksheet.write(x,21,line.monto_reg if line.monto_reg else '0.00',formats['numberdos'])
			worksheet.write(x,22,line.medio_pago if line.medio_pago else '',formats['especial1'])
			worksheet.write(x,23,line.ple_diario if line.ple_diario else '',formats['especial1'])
			worksheet.write(x,24,line.ple_compras if line.ple_compras else '',formats['especial1'])
			worksheet.write(x,25,line.ple_ventas if line.ple_ventas else '',formats['especial1'])
			x += 1

		widths = [9,9,7,11,8,10,10,10,5,7,11,13,47,4,11,40,3,16,12,12,12,12,12,12,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Libro_Diario.xlsx', 'rb')
		return self.env['popup.it'].get_file('Libro Diario.xlsx',base64.encodestring(b''.join(f.readlines())))

	def getCsv(self):
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		docname = 'LibroDiario.csv'

		#Get CSV
		sql_query = """	COPY (select * from account_journal_book)TO '"""+direccion+docname+"""'   WITH DELIMITER ',' CSV HEADER			
						"""
		self.env.cr.execute(sql_query)

		#Caracteres Especiales
		import importlib
		import sys
		importlib.reload(sys)

		f = open(direccion + docname, 'rb')		

		return self.env['popup.it'].get_file(docname,base64.encodestring(b''.join(f.readlines())))

	def getPdf(self):	
		#CREANDO ARCHIVO PDF
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		name_file = "Libro_Diario.pdf"
	
		archivo_pdf = SimpleDocTemplate(str(direccion)+name_file, pagesize=(2200,1000), rightMargin=30,leftMargin=30, topMargin=30,bottomMargin=18)

		elements = []
		#Estilos 
		style_title = ParagraphStyle(name = 'Center',alignment = TA_CENTER, fontSize = 40, fontName="Helvetica" )
		style_form = ParagraphStyle(name='Justify', alignment=TA_JUSTIFY , fontSize = 24, fontName="Helvetica" )
		style_left = ParagraphStyle(name = 'Left', alignment=TA_LEFT, fontSize=12, fontName="Helvetica")
		style_right = ParagraphStyle(name = 'Right', alignment=TA_RIGHT, fontSize=12, fontName="Helvetica")
		style_title_tab = ParagraphStyle(name = 'Center',alignment = TA_CENTER, fontSize = 13, fontName="Helvetica-Bold" )
		

		company = self.company_id
		texto = "Reporte Libro Diario"		
		elements.append(Paragraph(texto, style_title))
		elements.append(Spacer(1, 60))
		texto = 'Empresa: ' + (company.name)
		elements.append(Paragraph(texto, style_form))
		elements.append(Spacer(1, 12))
		texto = 'Dirección: ' + (company.street if company.street else '')
		elements.append(Paragraph(texto, style_form))
		elements.append(Spacer(1, 12))
		texto = 'Ruc: ' + (company.vat if company.vat else '')
		elements.append(Paragraph(texto, style_form))
		elements.append(Spacer(1, 12))
		texto = 'Rango Fecha: ' + str(self.date_ini) + ' - ' + str(self.date_end)
		elements.append(Paragraph(texto,style_form))
		elements.append(Spacer(1, 12))
		texto = 'Fecha de Reporte: ' + str(date.today()) 
		elements.append(Paragraph(texto, style_form))
		elements.append(Spacer(1, 80))


	#Crear Tabla
		headers = ['PERIODO','FECHA','LIBRO','VOUCHER','CUENTA','DEBE','HABER','BALANCE','MON','TC','IMP ME','CTA ANALIT','GLOSA','TDP',
				'RUC','PARTNER','TD','NRO COMP','F DOC','F VEN','C REG','MON REG','M PAGO','PLE DIARIO','PLE COMPRA','PLE VENTA','REG']

		datos = []
		datos.append([])

		for i in headers:
			datos[0].append(Paragraph(i,style_title_tab))

		for c,fila in enumerate(self.env['account.journal.book'].search([])):
			datos.append([])
			datos[c+1].append(Paragraph((fila['periodo']) if fila['periodo'] else '',style_left))
			datos[c+1].append(Paragraph((fila['fecha']) if fila['fecha'] else '',style_left))
			datos[c+1].append(Paragraph((fila['libro']) if fila['libro'] else '',style_left))
			datos[c+1].append(Paragraph((fila['voucher']) if fila['voucher'] else '',style_left))
			datos[c+1].append(Paragraph((fila['cuenta']) if fila['cuenta'] else '',style_left))
			datos[c+1].append(Paragraph(str(fila['debe']) if fila['debe'] else '0.00',style_right))
			datos[c+1].append(Paragraph(str(fila['haber']) if fila['haber'] else '0.00',style_right))
			datos[c+1].append(Paragraph(str(fila['balance']) if fila['balance'] else '0.00',style_right))
			datos[c+1].append(Paragraph((fila['moneda']) if fila['moneda'] else '',style_left))
			datos[c+1].append(Paragraph(str(fila['tc']) if fila['tc'] else '0.0000',style_right))
			datos[c+1].append(Paragraph(str(fila['importe_me']) if fila['importe_me'] else '0.00',style_right))
			datos[c+1].append(Paragraph((fila['code_cta_analitica']) if fila['code_cta_analitica'] else '',style_left))
			datos[c+1].append(Paragraph((fila['glosa']) if fila['glosa'] else '',style_left))
			datos[c+1].append(Paragraph((fila['td_partner']) if fila['td_partner'] else '',style_left))
			datos[c+1].append(Paragraph((fila['doc_partner']) if fila['doc_partner'] else '',style_left))
			datos[c+1].append(Paragraph((fila['partner']) if fila['partner'] else '',style_left))
			datos[c+1].append(Paragraph((fila['td_sunat']) if fila['td_sunat'] else '',style_left))
			datos[c+1].append(Paragraph((fila['nro_comprobante']) if fila['nro_comprobante'] else '',style_left))
			datos[c+1].append(Paragraph(str(fila['fecha_doc']) if fila['fecha_doc'] else '',style_left))
			datos[c+1].append(Paragraph(str(fila['fecha_ven']) if fila['fecha_ven'] else '',style_left))
			datos[c+1].append(Paragraph((fila['col_reg']) if fila['col_reg'] else '',style_left))
			datos[c+1].append(Paragraph(str(fila['monto_reg']) if fila['monto_reg'] else '0.000',style_right))
			datos[c+1].append(Paragraph((str(fila['medio_pago'])) if fila['medio_pago'] else '',style_left))
			datos[c+1].append(Paragraph((fila['ple_diario']) if fila['ple_diario'] else '',style_left))
			datos[c+1].append(Paragraph((fila['ple_compras']) if fila['ple_compras'] else '',style_left))
			datos[c+1].append(Paragraph((fila['ple_ventas']) if fila['ple_ventas'] else '',style_left))
			datos[c+1].append(Paragraph((str(fila['registro'])) if fila['registro'] else '',style_left))

		table_datos = Table(datos, colWidths=[2*cm,2*cm,2*cm,3*cm,2.6*cm,2.6*cm,2.6*cm,2.9*cm,1.5*cm,1.3*cm,2.4*cm,3.7*cm,6*cm,1.45*cm,3.2*cm,10*cm,
		1.2*cm,3.7*cm,2.75*cm,2.75*cm,2.4*cm,2*cm,2*cm,2.3*cm,2.3*cm,2.3*cm,2*cm])

		color_cab = colors.Color(red=(220/255),green=(230/255),blue=(241/255))

		#Estilo de Tabla
		style_table = TableStyle([
				('BACKGROUND', (0, 0), (26, 0),color_cab),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('GRID', (0,0), (-1,-1), 0.25, colors.black), 
				('BOX', (0,0), (-1,-1), 0.25, colors.black),
			])
		table_datos.setStyle(style_table)

		elements.append(table_datos)

		#Build
		archivo_pdf.build(elements)

		#Caracteres Especiales
		import importlib
		import sys
		importlib.reload(sys)
		import os

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file(name_file,base64.encodestring(b''.join(f.readlines())))

	@api.onchange('date_ini','date_end')
	def domain_dates(self):
		if self.date_ini:
			if self.exercise.date_from.year != self.date_ini.year:
				raise UserError("La fecha inicial no esta en el rango del Año Fiscal escogido (Ejercicio).")
		if self.date_end:
			if self.exercise.date_from.year != self.date_end.year:
				raise UserError("La fecha final no esta en el rango del Año Fiscal escogido (Ejercicio).")
		if self.date_ini and self.date_end:
			if self.date_end < self.date_ini:
				raise UserError("La fecha final no puede ser menor a la fecha inicial.")