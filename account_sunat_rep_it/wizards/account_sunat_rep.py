# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountSunatRep(models.TransientModel):
	_name = 'account.sunat.rep'

	name = fields.Char()

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=1)
	exercise = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	period = fields.Many2one('account.period',string='Periodo',required=True)

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			fiscal_year = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).fiscal_year
			if fiscal_year:
				self.exercise = fiscal_year.id
			else:
				raise UserError(u'No existe un año Fiscal configurado en Parametros Principales de Contabilidad para esta Compañía')
				
				
	def get_txt_81(self):
		return self._get_ple(1)

	def get_txt_82(self):
		return self._get_ple(2)

	def get_txt_141(self):
		return self._get_ple(3)

	def get_txt_diario(self):
		return self._get_ple(4)

	def get_txt_plan_c(self):
		return self._get_ple(5)

	def get_txt_mayor(self):
		return self._get_ple(6)

	def get_txt_servidores(self):
		FeeRep = self.env['account.fee.rep']
		return FeeRep.get_plame(1,self.period.date_start,self.period.date_end,self.company_id)
	
	def get_txt_recibos(self):
		FeeRep = self.env['account.fee.rep']		
		return FeeRep.get_plame(2,self.period.date_start,self.period.date_end,self.company_id)

	def _get_sql(self,type):
		PurchaseRep = self.env['account.purchase.rep']
		SaleRep = self.env['account.sale.rep']
		JournalRep = self.env['account.journal.rep']
		FeeRep = self.env['account.fee.rep']
		sql = ""
		nomenclatura = ""

		if type == 1:
			#SQL Compras 8.1
			sql = PurchaseRep._get_sql_ple81(self.period.date_start,self.period.date_end,self.company_id.id)
			nomenclatura = "080100"
		if type == 2:
			#SQL Compras 8.2
			sql = PurchaseRep._get_sql_ple82(self.period.date_start,self.period.date_end,self.company_id.id)
			nomenclatura = "080200"
		if type == 3:
			#SQL Ventas 14.1
			sql = SaleRep._get_sql_ple141(self.period.date_start,self.period.date_end,self.company_id.id)
			nomenclatura = "140100"
		if type == 4:
			#SQL Libro Diario
			sql = JournalRep._get_sql_ple(1,self.period.date_start,self.period.date_end,self.company_id.id)
			nomenclatura = "050100"
		if type == 5:
			#SQL Plan Contable
			sql = JournalRep._get_sql_ple(3,self.period.date_start,self.period.date_end,self.company_id.id)
			nomenclatura = "050300"
		if type == 6:
			#SQL Libro Mayor
			sql = JournalRep._get_sql_ple(2,self.period.date_start,self.period.date_end,self.company_id.id)
			nomenclatura = "060100"
		if type == 7:
			#SQL Rec de Honorarios
			sql = FeeRep._get_sql(self.period.date_start,self.period.date_end,self.company_id.id)

		return sql,nomenclatura

	def _get_ple(self,type):
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_ple_create_file
		ruc = self.company_id.partner_id.vat
		mond = self.company_id.currency_id.name

		if not direccion:
			raise UserError(u'No existe un Directorio PLE configurado en Parametros Principales de Contabilidad para su Compañía')

		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		if not mond:
			raise UserError('No configuro la moneda de su Compañia.')

		#LE + RUC + AÑO(YYYY) + MES(MM) + DIA(00) 
		name_doc = "LE"+str(ruc)+str(self.period.date_start.year)+str('{:02d}'.format(self.period.date_start.month))+"00"
		sql_ple,nomenclatura = self._get_sql(type)

		sql_query = """	COPY ("""+sql_ple+""")TO '"""+direccion+"""sunat.csv' WITH DELIMITER '|' """

		self.env.cr.execute(sql_query)

		#Caracteres Especiales
		import importlib
		import sys
		importlib.reload(sys)

		exp = ''.join(open(str(direccion + 'sunat.csv'),'r').readlines())

		# IDENTIFICADOR DEL LIBRO

		name_doc += nomenclatura

		# CODIGO DE OPORTUNIDAD DE PRESENTACION DEL EEFF (00) +
		# INDICADOR DE OPERACIONES (1) +
		# INDICADOR DE CONTENIDO Con informacion(1), Sin informacion(0) +
		# INDICADOR DE MONEDA UTILIZADA Nuevos Soles(1), US Dolares(2) +
		# INDICADOR DE LIBRO ELECTRONICO GENERADO POR EL PLE (1)

		name_doc += "00"+"1"+("1" if len(exp) > 0 else "0") + ("1" if mond == 'PEN' else "2") + "1.txt"

		return self.env['popup.it'].get_file(name_doc,base64.encodestring(b''.join(open(str(direccion + 'sunat.csv'),'rb').readlines()) if exp else b"== Sin Registros =="))	

	def get_excel_81(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Registro_de_Compras_81.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		sql_ple,nomenclatura = self._get_sql(1)

		worksheet = workbook.add_worksheet(nomenclatura)
		worksheet.set_tab_color('blue')

		HEADERS = ['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8','CAMPO 9','CAMPO 10','CAMPO 11','CAMPO 12',
					'CAMPO 13','CAMPO 14','CAMPO 15','CAMPO 16','CAMPO 17','CAMPO 18','CAMPO 19','CAMPO 20','CAMPO 21','CAMPO 22','CAMPO 23',
					'CAMPO 24','CAMPO 25','CAMPO 26','CAMPO 27','CAMPO 28','CAMPO 29','CAMPO 30','CAMPO 31','CAMPO 32','CAMPO 33','CAMPO 34',
					'CAMPO 35','CAMPO 36','CAMPO 37','CAMPO 38','CAMPO 39','CAMPO 40','CAMPO 41']

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		self.env.cr.execute(sql_ple)
		dicc = self.env.cr.dictfetchall()

		for line in dicc:
			worksheet.write(x,0,line['campo1'] if line['campo1'] else '',formats['especial1'])
			worksheet.write(x,1,line['campo2'] if line['campo2'] else '',formats['especial1'])
			worksheet.write(x,2,line['campo3'] if line['campo3'] else '',formats['especial1'])
			worksheet.write(x,3,line['campo4'] if line['campo4'] else '',formats['especial1'])
			worksheet.write(x,4,line['campo5'] if line['campo5'] else '',formats['especial1'])
			worksheet.write(x,5,line['campo6'] if line['campo6'] else '',formats['especial1'])
			worksheet.write(x,6,line['campo7'] if line['campo7'] else '',formats['especial1'])
			worksheet.write(x,7,line['campo8'] if line['campo8'] else '',formats['especial1'])
			worksheet.write(x,8,line['campo9'] if line['campo9'] else '',formats['especial1'])
			worksheet.write(x,9,line['campo10'] if line['campo10'] else '',formats['especial1'])
			worksheet.write(x,10,line['campo11'] if line['campo11'] else '',formats['especial1'])
			worksheet.write(x,11,line['campo12'] if line['campo12'] else '',formats['especial1'])
			worksheet.write(x,12,line['campo13'] if line['campo13'] else '',formats['especial1'])
			worksheet.write(x,13,line['campo14'] if line['campo14'] else '0.00',formats['numberdos'])
			worksheet.write(x,14,line['campo15'] if line['campo15'] else '0.00',formats['numberdos'])
			worksheet.write(x,15,line['campo16'] if line['campo16'] else '0.00',formats['numberdos'])
			worksheet.write(x,16,line['campo17'] if line['campo17'] else '0.00',formats['numberdos'])
			worksheet.write(x,17,line['campo18'] if line['campo18'] else '0.00',formats['numberdos'])
			worksheet.write(x,18,line['campo19'] if line['campo19'] else '0.00',formats['numberdos'])
			worksheet.write(x,19,line['campo20'] if line['campo20'] else '0.00',formats['numberdos'])
			worksheet.write(x,20,line['campo21'] if line['campo21'] else '0.00',formats['numberdos'])
			worksheet.write(x,21,line['campo22'] if line['campo22'] else '0.00',formats['numberdos'])
			worksheet.write(x,22,line['campo23'] if line['campo23'] else '0.00',formats['numberdos'])
			worksheet.write(x,23,line['campo24'] if line['campo24'] else '',formats['especial1'])
			worksheet.write(x,24,line['campo25'] if line['campo25'] else '0.0000',formats['numbercuatro'])
			worksheet.write(x,25,line['campo26'] if line['campo26'] else '',formats['especial1'])
			worksheet.write(x,26,line['campo27'] if line['campo27'] else '',formats['especial1'])
			worksheet.write(x,27,line['campo28'] if line['campo28'] else '',formats['especial1'])
			worksheet.write(x,28,line['campo29'] if line['campo29'] else '',formats['especial1'])
			worksheet.write(x,29,line['campo30'] if line['campo30'] else '',formats['especial1'])
			worksheet.write(x,30,line['campo31'] if line['campo31'] else '',formats['especial1'])
			worksheet.write(x,31,line['campo32'] if line['campo32'] else '',formats['especial1'])
			worksheet.write(x,32,line['campo33'] if line['campo33'] else '',formats['especial1'])
			worksheet.write(x,33,line['campo34'] if line['campo34'] else '',formats['especial1'])
			worksheet.write(x,34,line['campo35'] if line['campo35'] else '',formats['especial1'])
			worksheet.write(x,35,line['campo36'] if line['campo36'] else '',formats['especial1'])
			worksheet.write(x,36,line['campo37'] if line['campo37'] else '',formats['especial1'])
			worksheet.write(x,37,line['campo38'] if line['campo38'] else '',formats['especial1'])
			worksheet.write(x,38,line['campo39'] if line['campo39'] else '',formats['especial1'])
			worksheet.write(x,39,line['campo40'] if line['campo40'] else '',formats['especial1'])
			worksheet.write(x,40,line['campo41'] if line['campo41'] else '',formats['especial1'])
			x+=1

		
		widths = [10,22,12,12,12,12,12,12,12,12,12,12,50,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Registro_de_Compras_81.xlsx', 'rb')
		return self.env['popup.it'].get_file('Registro_de_Compras_81.xlsx',base64.encodestring(b''.join(f.readlines())))
			

	def get_excel_82(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Registro_de_Compras_82.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		sql_ple,nomenclatura = self._get_sql(2)

		worksheet = workbook.add_worksheet(nomenclatura)
		worksheet.set_tab_color('blue')

		HEADERS = ['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8','CAMPO 9','CAMPO 10','CAMPO 11','CAMPO 12',
					'CAMPO 13','CAMPO 14','CAMPO 15','CAMPO 16','CAMPO 17','CAMPO 18','CAMPO 19','CAMPO 20','CAMPO 21','CAMPO 22','CAMPO 23',
					'CAMPO 24','CAMPO 25','CAMPO 26','CAMPO 27','CAMPO 28','CAMPO 29','CAMPO 30','CAMPO 31','CAMPO 32','CAMPO 33','CAMPO 34',
					'CAMPO 35','CAMPO 36']

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		self.env.cr.execute(sql_ple)
		dicc = self.env.cr.dictfetchall()

		for line in dicc:
			worksheet.write(x,0,line['campo1'] if line['campo1'] else '',formats['especial1'])
			worksheet.write(x,1,line['campo2'] if line['campo2'] else '',formats['especial1'])
			worksheet.write(x,2,line['campo3'] if line['campo3'] else '',formats['especial1'])
			worksheet.write(x,3,line['campo4'] if line['campo4'] else '',formats['especial1'])
			worksheet.write(x,4,line['campo5'] if line['campo5'] else '',formats['especial1'])
			worksheet.write(x,5,line['campo6'] if line['campo6'] else '',formats['especial1'])
			worksheet.write(x,6,line['campo7'] if line['campo7'] else '',formats['especial1'])
			worksheet.write(x,7,line['campo8'] if line['campo8'] else '0.00',formats['numberdos'])
			worksheet.write(x,8,line['campo9'] if line['campo9'] else '0.00',formats['numberdos'])
			worksheet.write(x,9,line['campo10'] if line['campo10'] else '0.00',formats['numberdos'])
			worksheet.write(x,10,line['campo11'] if line['campo11'] else '',formats['especial1'])
			worksheet.write(x,11,line['campo12'] if line['campo12'] else '',formats['especial1'])
			worksheet.write(x,12,line['campo13'] if line['campo13'] else '',formats['especial1'])
			worksheet.write(x,13,line['campo14'] if line['campo14'] else '',formats['especial1'])
			worksheet.write(x,14,line['campo15'] if line['campo15'] else '',formats['especial1'])
			worksheet.write(x,15,line['campo16'] if line['campo16'] else '',formats['especial1'])
			worksheet.write(x,16,line['campo17'] if line['campo17'] else '0.0000',formats['numbercuatro'])
			worksheet.write(x,17,line['campo18'] if line['campo18'] else '',formats['especial1'])
			worksheet.write(x,18,line['campo19'] if line['campo19'] else '',formats['especial1'])
			worksheet.write(x,19,line['campo20'] if line['campo20'] else '',formats['especial1'])
			worksheet.write(x,20,line['campo21'] if line['campo21'] else '',formats['especial1'])
			worksheet.write(x,21,line['campo22'] if line['campo22'] else '',formats['especial1'])
			worksheet.write(x,22,line['campo23'] if line['campo23'] else '',formats['especial1'])
			worksheet.write(x,23,line['campo24'] if line['campo24'] else '',formats['especial1'])
			worksheet.write(x,24,line['campo25'] if line['campo25'] else '',formats['especial1'])
			worksheet.write(x,25,line['campo26'] if line['campo26'] else '',formats['especial1'])
			worksheet.write(x,26,line['campo27'] if line['campo27'] else '',formats['especial1'])
			worksheet.write(x,27,line['campo28'] if line['campo28'] else '',formats['especial1'])
			worksheet.write(x,28,line['campo29'] if line['campo29'] else '',formats['especial1'])
			worksheet.write(x,29,line['campo30'] if line['campo30'] else '',formats['especial1'])
			worksheet.write(x,30,line['campo31'] if line['campo31'] else '',formats['especial1'])
			worksheet.write(x,31,line['campo32'] if line['campo32'] else '',formats['especial1'])
			worksheet.write(x,32,line['campo33'] if line['campo33'] else '',formats['especial1'])
			worksheet.write(x,33,line['campo34'] if line['campo34'] else '',formats['especial1'])
			worksheet.write(x,34,line['campo35'] if line['campo35'] else '',formats['especial1'])
			worksheet.write(x,35,line['campo36'] if line['campo36'] else '',formats['especial1'])
			x+=1

		widths = [12,22,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,50,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Registro_de_Compras_82.xlsx', 'rb')
		return self.env['popup.it'].get_file('Registro_de_Compras_82.xlsx',base64.encodestring(b''.join(f.readlines())))

	
	def get_excel_141(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Registro_de_Ventas_141.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		sql_ple,nomenclatura = self._get_sql(3)

		worksheet = workbook.add_worksheet(nomenclatura)
		worksheet.set_tab_color('blue')

		HEADERS = ['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8','CAMPO 9','CAMPO 10','CAMPO 11','CAMPO 12',
					'CAMPO 13','CAMPO 14','CAMPO 15','CAMPO 16','CAMPO 17','CAMPO 18','CAMPO 19','CAMPO 20','CAMPO 21','CAMPO 22','CAMPO 23',
					'CAMPO 24','CAMPO 25','CAMPO 26','CAMPO 27','CAMPO 28','CAMPO 29','CAMPO 30','CAMPO 31','CAMPO 32','CAMPO 33','CAMPO 34']

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		self.env.cr.execute(sql_ple)
		dicc = self.env.cr.dictfetchall()

		for line in dicc:
			worksheet.write(x,0,line['campo1'] if line['campo1'] else '',formats['especial1'])
			worksheet.write(x,1,line['campo2'] if line['campo2'] else '',formats['especial1'])
			worksheet.write(x,2,line['campo3'] if line['campo3'] else '',formats['especial1'])
			worksheet.write(x,3,line['campo4'] if line['campo4'] else '',formats['especial1'])
			worksheet.write(x,4,line['campo5'] if line['campo5'] else '',formats['especial1'])
			worksheet.write(x,5,line['campo6'] if line['campo6'] else '',formats['especial1'])
			worksheet.write(x,6,line['campo7'] if line['campo7'] else '',formats['especial1'])
			worksheet.write(x,7,line['campo8'] if line['campo8'] else '',formats['especial1'])
			worksheet.write(x,8,line['campo9'] if line['campo9'] else '',formats['especial1'])
			worksheet.write(x,9,line['campo10'] if line['campo10'] else '',formats['especial1'])
			worksheet.write(x,10,line['campo11'] if line['campo11'] else '',formats['especial1'])
			worksheet.write(x,11,line['campo12'] if line['campo12'] else '',formats['especial1'])
			worksheet.write(x,12,line['campo13'] if line['campo13'] else '0.00',formats['numberdos'])
			worksheet.write(x,13,line['campo14'] if line['campo14'] else '0.00',formats['numberdos'])
			worksheet.write(x,14,line['campo15'] if line['campo15'] else '0.00',formats['numberdos'])
			worksheet.write(x,15,line['campo16'] if line['campo16'] else '0.00',formats['numberdos'])
			worksheet.write(x,16,line['campo17'] if line['campo17'] else '0.00',formats['numberdos'])
			worksheet.write(x,17,line['campo18'] if line['campo18'] else '0.00',formats['numberdos'])
			worksheet.write(x,18,line['campo19'] if line['campo19'] else '0.00',formats['numberdos'])
			worksheet.write(x,19,line['campo20'] if line['campo20'] else '0.00',formats['numberdos'])
			worksheet.write(x,20,line['campo21'] if line['campo21'] else '0.00',formats['numberdos'])
			worksheet.write(x,21,line['campo22'] if line['campo22'] else '0.00',formats['numberdos'])
			worksheet.write(x,22,line['campo23'] if line['campo23'] else '0.00',formats['numberdos'])
			worksheet.write(x,23,line['campo24'] if line['campo24'] else '0.00',formats['numberdos'])
			worksheet.write(x,24,line['campo25'] if line['campo25'] else '',formats['especial1'])
			worksheet.write(x,25,line['campo26'] if line['campo26'] else '0.00',formats['numbercuatro'])
			worksheet.write(x,26,line['campo27'] if line['campo27'] else '',formats['especial1'])
			worksheet.write(x,27,line['campo28'] if line['campo28'] else '',formats['especial1'])
			worksheet.write(x,28,line['campo29'] if line['campo29'] else '',formats['especial1'])
			worksheet.write(x,29,line['campo30'] if line['campo30'] else '',formats['especial1'])
			worksheet.write(x,30,line['campo31'] if line['campo31'] else '',formats['especial1'])
			worksheet.write(x,31,line['campo32'] if line['campo32'] else '',formats['especial1'])
			worksheet.write(x,32,line['campo33'] if line['campo33'] else '',formats['especial1'])
			worksheet.write(x,33,line['campo34'] if line['campo34'] else '',formats['especial1'])
			x+=1

		widths = [12,22,12,12,12,12,12,12,12,12,12,50,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Registro_de_Ventas_141.xlsx', 'rb')
		return self.env['popup.it'].get_file('Registro_de_Ventas_141.xlsx',base64.encodestring(b''.join(f.readlines())))


	def get_excel_diario(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Ple_Libro_Diario.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		sql_ple,nomenclatura = self._get_sql(4)

		worksheet = workbook.add_worksheet(nomenclatura)
		worksheet.set_tab_color('blue')

		HEADERS = ['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8','CAMPO 9','CAMPO 10','CAMPO 11','CAMPO 12',
					'CAMPO 13','CAMPO 14','CAMPO 15','CAMPO 16','CAMPO 17','CAMPO 18','CAMPO 19','CAMPO 20','CAMPO 21']

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		self.env.cr.execute(sql_ple)
		dicc = self.env.cr.dictfetchall()

		for line in dicc:
			worksheet.write(x,0,line['campo1'] if line['campo1'] else '',formats['especial1'])
			worksheet.write(x,1,line['campo2'] if line['campo2'] else '',formats['especial1'])
			worksheet.write(x,2,line['campo3'] if line['campo3'] else '',formats['especial1'])
			worksheet.write(x,3,line['campo4'] if line['campo4'] else '',formats['especial1'])
			worksheet.write(x,4,line['campo5'] if line['campo5'] else '',formats['especial1'])
			worksheet.write(x,5,line['campo6'] if line['campo6'] else '',formats['especial1'])
			worksheet.write(x,6,line['campo7'] if line['campo7'] else '',formats['especial1'])
			worksheet.write(x,7,line['campo8'] if line['campo8'] else '',formats['especial1'])
			worksheet.write(x,8,line['campo9'] if line['campo9'] else '',formats['especial1'])
			worksheet.write(x,9,line['campo10'] if line['campo10'] else '',formats['especial1'])
			worksheet.write(x,10,line['campo11'] if line['campo11'] else '',formats['especial1'])
			worksheet.write(x,11,line['campo12'] if line['campo12'] else '',formats['especial1'])
			worksheet.write(x,12,line['campo13'] if line['campo13'] else '',formats['especial1'])
			worksheet.write(x,13,line['campo14'] if line['campo14'] else '',formats['especial1'])
			worksheet.write(x,14,line['campo15'] if line['campo15'] else '',formats['especial1'])
			worksheet.write(x,15,line['campo16'] if line['campo16'] else '',formats['especial1'])
			worksheet.write(x,16,line['campo17'] if line['campo17'] else '',formats['especial1'])
			worksheet.write(x,17,line['campo18'] if line['campo18'] else '0.00',formats['numberdos'])
			worksheet.write(x,18,line['campo19'] if line['campo19'] else '0.00',formats['numberdos'])
			worksheet.write(x,19,line['campo20'] if line['campo20'] else '',formats['especial1'])
			worksheet.write(x,20,line['campo21'] if line['campo21'] else '',formats['especial1'])
			x+=1

		widths = [12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,42,12,12,12,30,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Ple_Libro_Diario.xlsx', 'rb')
		return self.env['popup.it'].get_file('Ple_Libro_Diario.xlsx',base64.encodestring(b''.join(f.readlines())))


	def get_excel_plan_c(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Ple_Plan_Contable.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		sql_ple,nomenclatura = self._get_sql(5)

		worksheet = workbook.add_worksheet(nomenclatura)
		worksheet.set_tab_color('blue')

		HEADERS = ['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8']

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		self.env.cr.execute(sql_ple)
		dicc = self.env.cr.dictfetchall()

		for line in dicc:
			worksheet.write(x,0,line['campo1'] if line['campo1'] else '',formats['especial1'])
			worksheet.write(x,1,line['campo2'] if line['campo2'] else '',formats['especial1'])
			worksheet.write(x,2,line['campo3'] if line['campo3'] else '',formats['especial1'])
			worksheet.write(x,3,line['campo4'] if line['campo4'] else '',formats['especial1'])
			worksheet.write(x,4,line['campo5'] if line['campo5'] else '',formats['especial1'])
			worksheet.write(x,5,line['campo6'] if line['campo6'] else '',formats['especial1'])
			worksheet.write(x,6,line['campo7'] if line['campo7'] else '',formats['especial1'])
			worksheet.write(x,7,line['campo8'] if line['campo8'] else '',formats['especial1'])
			x+=1

		widths = [12,12,57,12,12,12,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Ple_Plan_Contable.xlsx', 'rb')
		return self.env['popup.it'].get_file('Ple_Plan_Contable.xlsx',base64.encodestring(b''.join(f.readlines())))

	def get_excel_mayor(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Ple_Mayor.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		sql_ple,nomenclatura = self._get_sql(6)

		worksheet = workbook.add_worksheet(nomenclatura)
		worksheet.set_tab_color('blue')

		HEADERS = ['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8','CAMPO 9','CAMPO 10','CAMPO 11','CAMPO 12',
					'CAMPO 13','CAMPO 14','CAMPO 15','CAMPO 16','CAMPO 17','CAMPO 18','CAMPO 19','CAMPO 20','CAMPO 21']

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		self.env.cr.execute(sql_ple)
		dicc = self.env.cr.dictfetchall()

		for line in dicc:
			worksheet.write(x,0,line['campo1'] if line['campo1'] else '',formats['especial1'])
			worksheet.write(x,1,line['campo2'] if line['campo2'] else '',formats['especial1'])
			worksheet.write(x,2,line['campo3'] if line['campo3'] else '',formats['especial1'])
			worksheet.write(x,3,line['campo4'] if line['campo4'] else '',formats['especial1'])
			worksheet.write(x,4,line['campo5'] if line['campo5'] else '',formats['especial1'])
			worksheet.write(x,5,line['campo6'] if line['campo6'] else '',formats['especial1'])
			worksheet.write(x,6,line['campo7'] if line['campo7'] else '',formats['especial1'])
			worksheet.write(x,7,line['campo8'] if line['campo8'] else '',formats['especial1'])
			worksheet.write(x,8,line['campo9'] if line['campo9'] else '',formats['especial1'])
			worksheet.write(x,9,line['campo10'] if line['campo10'] else '',formats['especial1'])
			worksheet.write(x,10,line['campo11'] if line['campo11'] else '',formats['especial1'])
			worksheet.write(x,11,line['campo12'] if line['campo12'] else '',formats['especial1'])
			worksheet.write(x,12,line['campo13'] if line['campo13'] else '',formats['especial1'])
			worksheet.write(x,13,line['campo14'] if line['campo14'] else '',formats['especial1'])
			worksheet.write(x,14,line['campo15'] if line['campo15'] else '',formats['especial1'])
			worksheet.write(x,15,line['campo16'] if line['campo16'] else '',formats['especial1'])
			worksheet.write(x,16,line['campo17'] if line['campo17'] else '',formats['especial1'])
			worksheet.write(x,17,line['campo18'] if line['campo18'] else '0.00',formats['numberdos'])
			worksheet.write(x,18,line['campo19'] if line['campo19'] else '0.00',formats['numberdos'])
			worksheet.write(x,19,line['campo20'] if line['campo20'] else '',formats['especial1'])
			worksheet.write(x,20,line['campo21'] if line['campo21'] else '',formats['especial1'])
			x+=1

		widths = [12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,42,12,12,12,28,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Ple_Mayor.xlsx', 'rb')
		return self.env['popup.it'].get_file('Ple_Mayor.xlsx',base64.encodestring(b''.join(f.readlines())))
		

	def get_excel_servidores(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Servidores.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		sql_ple,nomenclatura = self._get_sql(7)

		worksheet = workbook.add_worksheet("Servidores")
		worksheet.set_tab_color('blue')

		HEADERS = ['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7']

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		self.env.cr.execute(sql_ple)
		dicc = self.env.cr.dictfetchall()

		for line in dicc:
			worksheet.write(x,0,line['tdp'] if line['tdp'] else '',formats['especial1'])
			worksheet.write(x,1,line['docp'] if line['docp'] else '',formats['especial1'])
			worksheet.write(x,2,line['apellido_p'] if line['apellido_p'] else '',formats['especial1'])
			worksheet.write(x,3,line['apellido_m'] if line['apellido_m'] else '',formats['especial1'])
			worksheet.write(x,4,line['namep'] if line['namep'] else '',formats['especial1'])
			worksheet.write(x,5,line['is_not_home'] if line['is_not_home'] else '',formats['especial1'])
			worksheet.write(x,6,line['c_d_imp'] if line['c_d_imp'] else '0',formats['especial1'])
			x+=1

		widths = [9,12,26,26,52,10,10]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Servidores.xlsx', 'rb')
		return self.env['popup.it'].get_file('Servidores.xlsx',base64.encodestring(b''.join(f.readlines())))

	def get_excel_recibos(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Recibos.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		sql_ple,nomenclatura = self._get_sql(7)

		worksheet = workbook.add_worksheet("Recibos")
		worksheet.set_tab_color('blue')

		HEADERS = ['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8','CAMPO 9','CAMPO 10','CAMPO 11']

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		self.env.cr.execute(sql_ple)
		dicc = self.env.cr.dictfetchall()

		for line in dicc:
			worksheet.write(x,0,line['tdp'] if line['tdp'] else '',formats['especial1'])
			worksheet.write(x,1,line['docp'] if line['docp'] else '',formats['especial1'])
			worksheet.write(x,2,'R',formats['especial1'])
			worksheet.write(x,3,line['serie'] if line['serie'] else '',formats['especial1'])
			worksheet.write(x,4,line['numero'] if line['numero'] else '',formats['especial1'])
			worksheet.write(x,5,line['renta'] if line['renta'] else '0.00',formats['numberdos'])
			worksheet.write(x,6,line['fecha_e'] if line['fecha_e'] else '',formats['dateformat'])
			worksheet.write(x,7,line['fecha_p'] if line['fecha_p'] else '',formats['dateformat'])
			worksheet.write(x,8,'0' if line['retencion'] == 0 else '1',formats['especial1'])
			worksheet.write(x,9,'',formats['especial1'])
			worksheet.write(x,10,'',formats['especial1'])
			x+=1

		widths = [9,12,12,12,12,12,12,12,12,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Recibos.xlsx', 'rb')
		return self.env['popup.it'].get_file('Recibos.xlsx',base64.encodestring(b''.join(f.readlines())))
