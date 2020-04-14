# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import base64

class AccountBankStatement(models.Model):
	_inherit = 'account.bank.statement'

	def generate_excel(self):
		import io
		from xlsxwriter.workbook import Workbook

		ReportBase = self.env['report.base']
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Extractos_Bancarios.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("EXTRACTOS BANCARIOS")
		worksheet.set_tab_color('blue')

		worksheet.set_row(1,60)

		name_ext = self.name if self.name else ''

		formats['numberdosespecial'].set_num_format('"%s" #,##0.00' % self.currency_id.symbol)
		formats['numberdos'].set_num_format('"%s" #,##0.00' % self.currency_id.symbol)

		worksheet.merge_range(1,1,1,6, "EXTRACTO BANCARIO"+"\n"+name_ext, formats['especial3'])

		worksheet.write(3,1, "Diario:", formats['especial2'])
		worksheet.write(4,1, "Fecha:", formats['especial2'])
		worksheet.write(3,5, "Saldo Inicial:", formats['especial2'])
		worksheet.write(4,5, "Balance Final:", formats['especial2'])

		worksheet.write(3,2, self.journal_id.name, formats['especial4'])
		worksheet.write(4,2, self.date, formats['especialdate'])
		worksheet.write_number(3,6, self.balance_start , formats['numberdosespecial'])
		worksheet.write_number(4,6, self.balance_end_real, formats['numberdosespecial'])

		HEADERS = ['FECHA','ETIQUETA','PARTNER','REFERENCIA','MEDIO DE PAGO','CANTIDAD']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,6,1,formats['boldbord'])

		x=7

		for line in self.line_ids:
			worksheet.write(x,1,line.date if line.date else '',formats['dateformat'])
			worksheet.write(x,2,line.name if line.name else '',formats['especial1'])
			worksheet.write(x,3,line.partner_id.name if line.partner_id else '',formats['especial1'])
			worksheet.write(x,4,line.ref if line.ref else '',formats['especial1'])
			worksheet.write(x,5,line.catalog_payment_id.name if line.catalog_payment_id else '',formats['especial1'])
			worksheet.write_number(x,6,line.amount if line.amount else '0.00',formats['numberdos'])
			x += 1

		widths = [4,10,25,25,23,20,15]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Extractos_Bancarios.xlsx', 'rb')

		return self.env['popup.it'].get_file('Extractos_Bancarios.xlsx',base64.encodestring(b''.join(f.readlines())))

