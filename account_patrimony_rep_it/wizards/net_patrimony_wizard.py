# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64
from lxml import etree
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
ENV_GROUPS = [
			{'name': 'ACTIVIDADES DE OPERACION' ,'code': ['E1','E2'], 'total_name': 'AUMENTO (DISM) DEL EFECTIVO Y EQUIVALENTE DE EFECTIVO PROVENIENTES DE ACTIVIDADES DE OPERACION'},
			{'name': 'ACTIVIDADES DE INVERSION' ,'code': ['E3','E4'], 'total_name': 'AUMENTO (DISM) DEL EFECTIVO Y EQUIVALENTE DE EFECTIVO PROVENIENTES DE ACTIVIDADES DE INVERSION'},
			{'name': 'ACTIVIDADES DE FINANCIAMIENTO' ,'code': ['E5','E6'], 'total_name': 'AUMENTO (DISM) DEL EFECTIVO Y EQUIVALENTE DE EFECTIVO PROVENIENTES DE ACTIVIDADES DE FINANCIAMIENTO'}
		]

class NetPatrimonyWizard(models.TransientModel):
	_name = 'net.patrimony.wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True,default=1)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string='Ejercicio',required=True)
	period_from = fields.Many2one('account.period',string='Periodo Inicial',required=True)
	period_to = fields.Many2one('account.period',string='Periodo Final',required=True)

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			fiscal_year = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).fiscal_year
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id
			else:
				raise UserError(u'No existe un año Fiscal configurado en Parametros Principales de Contabilidad para esta Compañía')

	def _get_net_patrimony_sql(self):
		names = self.env['account.patrimony.type'].search([],order='id').mapped('name')
		processed_names = ['name character varying']
		for name in names:
			processed_names.append(name.replace(' ','_') + ' numeric')
		sql = """
			select * from crosstab(
				$$
					select
					aml.name,
					apt.name as patrimony,
					sum(vd.haber - vd.debe) as total
					from vst_diariog vd
					left join account_move_line aml on aml.id = vd.move_line_id
					left join account_account aa on aa.id = aml.account_id
					inner join account_patrimony_type apt on apt.id = aa.patrimony_id
					inner join account_period ap on substring(ap.code,5,8)::int >= substring('{period_from}',5,8)::int 
												 and substring(ap.code,5,8)::int <= substring('{period_to}',5,8)::int
					where vd.periodo = ap.code 
					and aa.company_id = {company}
					group by aml.name, apt.name, apt.id
					order by 1,2 
				$$,
				$$
					select name from account_patrimony_type
				$$
			) AS ({names})
		""".format(
				period_from = self.period_from.code,
				period_to = self.period_to.code,
				company = self.company_id.id,
				names = ','.join(processed_names)
			)
		return sql

	def get_excel_net_patrimony(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion + 'Patrimonio_Neto.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Patrimonio Neto")
		worksheet.set_tab_color('blue')

		worksheet.write(1,1,self.company_id.name,formats['especial2'])
		worksheet.write(2,1,'ESTADO DE CAMBIOS EN EL PATRIMONIO NETO AL %s' % self.period_to.date_end,formats['especial2'])
		worksheet.write(3,1,'(Expresado en Nuevos Soles)',formats['especial2'])		
		
		self._cr.execute(self._get_net_patrimony_sql())
		data = self._cr.dictfetchall()
		x, y = 5, 2
		limit = len(data[0] if data else 0)
		names = self.env['account.patrimony.type'].search([],order='id').mapped('name')
		size = len(names) + 1
		worksheet.write(x, 1, 'CONCEPTOS', formats['boldbord'])
		for name in names:
			worksheet.write(x, y, name, formats['boldbord'])
			y += 1
		worksheet.write(x, y, 'TOTALES', formats['boldbord'])
		x += 1
		names = [name.lower().replace(' ', '_') for name in names]
		total_col = 0
		table = []
		for line in data:
			worksheet.write(x, 1, line['name'] if line['name'] else '', formats['especial1'])
			y, total_row, row = 2, 0, []
			for name in names:
				aux = line[name] if line[name] else 0.0
				worksheet.write(x, y, aux, formats['numberdos'])
				total_row += aux
				row.append(aux)
				y += 1
			table.append(row)
			worksheet.write(x, y, total_row, formats['numberdos'])
			total_col += total_row
			x += 1
		worksheet.write(x, 1, 'TOTALES', formats['boldbord'])
		worksheet.write(x, y, total_col, formats['numbertotal'])
		zipped_table = zip(*table)
		y = 2
		for row in zipped_table:
			worksheet.write(x, y, sum(list(row)), formats['numbertotal'])
			y += 1
		widths = [10,57] + size * [19]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Patrimonio_Neto.xlsx', 'rb')
		return self.env['popup.it'].get_file('Patrimonio_Neto.xlsx',base64.encodestring(b''.join(f.readlines())))