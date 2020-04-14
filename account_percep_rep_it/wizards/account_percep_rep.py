# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountPercepRep(models.TransientModel):
	_name = 'account.percep.rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=1)
	exercise = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	date_ini = fields.Date(string=u'Fecha Inicial',required=True)
	date_end = fields.Date(string=u'Fecha Final',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en', required=True,default='pantalla')
	type =  fields.Selection([('solo','Solo Percepciones'),('det','Detalle Percepciones')],string=u'Mostrar', required=True,default='solo')

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

	def get_report(self):
		if self.type == 'solo':
			self.env.cr.execute("""
			CREATE OR REPLACE view account_percep_sp_book as ("""+self._get_sql()+""")""")
			if self.type_show == 'pantalla':
				return {
					'name': 'Solo Percepciones',
					'type': 'ir.actions.act_window',
					'res_model': 'account.percep.sp.book',
					'view_mode': 'tree',
					'view_type': 'form',
					'views': [(False, 'tree')],
				}
			if self.type_show == 'excel':
				return self.get_excel()
				
		if self.type == 'det':
			self.env.cr.execute("""
			CREATE OR REPLACE view account_percep_book as ("""+self._get_sql()+""")""")
			if self.type_show == 'pantalla':
				return {
					'name': 'Detalle Percepciones',
					'type': 'ir.actions.act_window',
					'res_model': 'account.percep.book',
					'view_mode': 'tree',
					'view_type': 'form',
					'views': [(False, 'tree')],
				}
			if self.type_show == 'excel':
				return self.get_excel()

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		if self.type == 'solo':
			namefile = 'Solo_Percepciones.xlsx'
		if self.type == 'det':
			namefile = 'Detalle_Percepciones.xlsx'
		
		workbook = Workbook(direccion + namefile)
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		if self.type == 'solo':
			##########SOLO PERCEPCIONES############
			worksheet = workbook.add_worksheet("SOLO PERCEPCIONES")
		if self.type == 'det':
			##########DETALLE PERCEPCIONES############
			worksheet = workbook.add_worksheet("DETALLE PERCEPCIONES")

		worksheet.set_tab_color('blue')

		HEADERS = ['PERIODO CON','FECHA PERC','FECHA USO','LIBRO','VOUCHER','TDP','RUC','PARTNER','SERIE',u'NÚMERO','FECHA COM PER','PERCEPCION']

		if self.type == 'det':
			HEADERS.append('NRO COMP')
			HEADERS.append('FECHA CP')
			HEADERS.append('MONTO')

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		if self.type == 'solo':
			dic = self.env['account.percep.sp.book'].search([])
		if self.type == 'det':
			dic = self.env['account.percep.book'].search([])

		for line in dic:
			worksheet.write(x,0,line.periodo_con if line.periodo_con else '',formats['especial1'])
			worksheet.write(x,1,line.periodo_percep if line.periodo_percep else '',formats['especial1'])
			worksheet.write(x,2,line.fecha_uso if line.fecha_uso else '',formats['dateformat'])
			worksheet.write(x,3,line.libro if line.libro else '',formats['especial1'])
			worksheet.write(x,4,line.voucher if line.voucher else '',formats['especial1'])
			worksheet.write(x,5,line.tipo_per if line.tipo_per else '',formats['especial1'])
			worksheet.write(x,6,line.ruc_agente if line.ruc_agente else '',formats['especial1'])
			worksheet.write(x,7,line.partner if line.partner else '',formats['especial1'])
			worksheet.write(x,8,line.serie_cp if line.serie_cp else '',formats['especial1'])
			worksheet.write(x,9,line.numero_cp if line.numero_cp else '',formats['especial1'])
			worksheet.write(x,10,line.fecha_com_per if line.fecha_com_per else '',formats['dateformat'])
			worksheet.write(x,11,line.percepcion if line.percepcion else '0.00',formats['numberdos'])
			if self.type == 'det':
				worksheet.write(x,12,line.nro_comprobante if line.nro_comprobante else '',formats['especial1'])
				worksheet.write(x,13,line.fecha_cp if line.fecha_cp else '',formats['dateformat'])
				worksheet.write(x,14,line.montof if line.montof else '0.00',formats['numberdos'])
			x += 1

		widths = [9,9,12,7,11,4,11,40,6,10,12,10]

		if self.type == 'det':
				widths.append(13)
				widths.append(12)
				widths.append(10)

		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion + namefile, 'rb')
		return self.env['popup.it'].get_file(namefile,base64.encodestring(b''.join(f.readlines())))

	def _get_sql(self):

		if self.type == 'solo':
			sql = """select *
				from vst_percepciones_sp
				where (fecha_uso between '%s' and '%s')
				and company_id = %s 
			""" % (self.date_ini.strftime('%Y/%m/%d'),
				self.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))
			return sql

		if self.type == 'det':
			sql = """select *
				from vst_percepciones
				where (fecha_uso between '%s' and '%s')
				and company_id = %s 
			""" % (self.date_ini.strftime('%Y/%m/%d'),
				self.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))
			return sql

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
	