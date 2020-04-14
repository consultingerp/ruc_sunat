# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountSaleeRep(models.TransientModel):
	_name = 'account.sale.rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=1)
	exercise = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	date_ini = fields.Date(string=u'Fecha Inicial',required=True)
	date_end = fields.Date(string=u'Fecha Final',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('csv','CSV')],string=u'Mostrar en',default='pantalla')
	ple_format = fields.Selection([('0','14.1')],string=u'Formato PLE')

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
		if self.type_show:
			self.env.cr.execute("""
				CREATE OR REPLACE view account_sale_book as ("""+self._get_sql()+""")""")
				
			if self.type_show == 'pantalla':
				return {
					'name': 'Registro Ventas',
					'type': 'ir.actions.act_window',
					'res_model': 'account.sale.book',
					'view_mode': 'tree',
					'view_type': 'form',
					'views': [(False, 'tree')],
				}

			if self.type_show == 'excel':
				return self.get_excel()
			
			if self.type_show == 'csv':
				return self.getCsv()
		else:
			raise UserError("Es que complete el campo Mostrar en")

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Registro_Ventas.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########REGISTRO VENTAS############
		worksheet = workbook.add_worksheet("REGISTRO VENTAS")
		worksheet.set_tab_color('blue')

		HEADERS = ['PERIODO','FECHA CONT','LIBRO','VOUCHER','FECHA EM','FECHA VEN','TD','SERIE',u'AÑO',u'NÚMERO','TDP','RUC','PARTNER',
		'EXP','VENTA G','INAF','EXO','ISC V','OTROS V','IGV','TOTAL','MON','MONTO ME','TC','FECHA DET','COMP DET',
		'FECHA DOC M','TD DOC M','SERIE M','NUMERO M','GLOSA']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		#DECLARANDO TOTALES
		exp, venta_g, inaf, exo, isc_v, otros_v, igv_v, total = 0, 0, 0, 0, 0, 0, 0, 0

		for line in self.env['account.sale.book'].search([]):
			worksheet.write(x,0,line.periodo if line.periodo else '',formats['especial1'])
			worksheet.write(x,1,line.fecha_cont if line.fecha_cont else '',formats['dateformat'])
			worksheet.write(x,2,line.libro if line.libro else '',formats['especial1'])
			worksheet.write(x,3,line.voucher if line.voucher else '',formats['especial1'])
			worksheet.write(x,4,line.fecha_e if line.fecha_e else '',formats['dateformat'])
			worksheet.write(x,5,line.fecha_v if line.fecha_v else '',formats['dateformat'])
			worksheet.write(x,6,line.td if line.td else '',formats['especial1'])
			worksheet.write(x,7,line.serie if line.serie else '',formats['especial1'])
			worksheet.write(x,8,line.anio if line.anio else '',formats['especial1'])
			worksheet.write(x,9,line.numero if line.numero else '',formats['especial1'])
			worksheet.write(x,10,line.tdp if line.tdp else '',formats['especial1'])
			worksheet.write(x,11,line.docp if line.docp else '',formats['especial1'])
			worksheet.write(x,12,line.namep if line.namep else '',formats['especial1'])
			worksheet.write(x,13,line.exp if line.exp else '0.00',formats['numberdos'])
			worksheet.write(x,14,line.venta_g if line.venta_g else '0.00',formats['numberdos'])
			worksheet.write(x,15,line.inaf if line.inaf else '0.00',formats['numberdos'])
			worksheet.write(x,16,line.exo if line.exo else '0.00',formats['numberdos'])
			worksheet.write(x,17,line.isc_v if line.isc_v else '0.00',formats['numberdos'])
			worksheet.write(x,18,line.otros_v if line.otros_v else '0.00',formats['numberdos'])
			worksheet.write(x,19,line.igv_v if line.igv_v else '0.00',formats['numberdos'])
			worksheet.write(x,20,line.total if line.total else '0.00',formats['numberdos'])
			worksheet.write(x,21,line.name if line.name else '',formats['especial1'])
			worksheet.write(x,22,line.monto_me if line.monto_me else '0.00',formats['numberdos'])
			worksheet.write(x,23,line.currency_rate if line.currency_rate else '0.0000',formats['numbercuatro'])
			worksheet.write(x,24,line.fecha_det if line.fecha_det else '',formats['dateformat'])
			worksheet.write(x,25,line.comp_det if line.comp_det else '',formats['especial1'])
			worksheet.write(x,26,line.f_doc_m if line.f_doc_m else '',formats['dateformat'])
			worksheet.write(x,27,line.td_doc_m if line.td_doc_m else '',formats['especial1'])
			worksheet.write(x,28,line.serie_m if line.serie_m else '',formats['especial1'])
			worksheet.write(x,29,line.numero_m if line.numero_m else '',formats['especial1'])
			worksheet.write(x,30,line.glosa if line.glosa else '',formats['especial1'])
			x += 1

			exp += line.exp if line.exp else 0
			venta_g += line.venta_g if line.venta_g else 0
			inaf += line.inaf if line.inaf else 0
			exo += line.exo if line.exo else 0
			isc_v += line.isc_v if line.isc_v else 0
			otros_v += line.otros_v if line.otros_v else 0
			igv_v += line.igv_v if line.igv_v else 0
			total += line.total if line.total else 0

		worksheet.write(x,13,exp,formats['numbertotal'])
		worksheet.write(x,14,venta_g,formats['numbertotal'])
		worksheet.write(x,15,inaf,formats['numbertotal'])
		worksheet.write(x,16,exo,formats['numbertotal'])
		worksheet.write(x,17,isc_v,formats['numbertotal'])
		worksheet.write(x,18,otros_v,formats['numbertotal'])
		worksheet.write(x,19,igv_v,formats['numbertotal'])
		worksheet.write(x,20,total,formats['numbertotal'])

		widths = [9,12,7,11,10,10,3,10,10,10,4,11,40,10,10,10,10,10,10,10,12,5,12,7,12,12,12,12,12,12,47]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Registro_Ventas.xlsx', 'rb')
		return self.env['popup.it'].get_file('Registro_Ventas.xlsx',base64.encodestring(b''.join(f.readlines())))

	def getCsv(self):
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		docname = 'RegistroVentas.csv'

		#Get CSV
		sql_query = """	COPY (select * from account_sale_book)TO '"""+direccion+docname+"""'   WITH DELIMITER ',' CSV HEADER			
						"""
		self.env.cr.execute(sql_query)

		#Caracteres Especiales
		import importlib
		import sys
		importlib.reload(sys)

		f = open(direccion + docname, 'rb')		

		return self.env['popup.it'].get_file(docname,base64.encodestring(b''.join(f.readlines())))


	def get_ple(self):
		if not self.ple_format:
			raise UserError('no selecciono un Formato PLE')
		else:
			direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_ple_create_file

			if not direccion:
				raise UserError(u'No existe un Directorio PLE configurado en Parametros Principales de Contabilidad para su Compañía')
			ruc = self.company_id.partner_id.vat
			mond = self.company_id.currency_id.name

			if not ruc:
				raise UserError('No configuro el RUC de su Compañia.')

			if not mond:
				raise UserError('No configuro la moneda de su Compañia.')

			#LE + RUC + AÑO(YYYY) + MES(MM) + DIA(00) 
			name_doc = "LE"+str(ruc)+str(self.date_ini.year)+str('{:02d}'.format(self.date_ini.month))+"00"
			
			#SI ES 14.1
			if self.ple_format == '0':
				#Get CSV
				sql_query = """	COPY ("""+self._get_sql_ple141(self.date_ini,self.date_end,self.company_id.id)+""")TO '"""+direccion+"""sale.csv' WITH DELIMITER '|' """

			self.env.cr.execute(sql_query)

			#Caracteres Especiales
			import importlib
			import sys
			importlib.reload(sys)

			exp = ''.join(open(str(direccion + 'sale.csv'),'r').readlines())

			# IDENTIFICADOR DEL LIBRO

			if self.ple_format == '0':
				name_doc += "140100"

			# CODIGO DE OPORTUNIDAD DE PRESENTACION DEL EEFF (00) +
			# INDICADOR DE OPERACIONES (1) +
			# INDICADOR DE CONTENIDO Con informacion(1), Sin informacion(0) +
			# INDICADOR DE MONEDA UTILIZADA Nuevos Soles(1), US Dolares(2) +
			# INDICADOR DE LIBRO ELECTRONICO GENERADO POR EL PLE (1)

			name_doc += "00"+"1"+("1" if len(exp) > 0 else "0") + ("1" if mond == 'PEN' else "2") + "1.txt"

			return self.env['popup.it'].get_file(name_doc,base64.encodestring(b''.join(open(str(direccion + 'sale.csv'),'rb').readlines()) if exp else b"== Sin Registros =="))	

	def _get_sql_ple141(self,x_date_ini,x_date_end,x_company_id):
		sql = """SELECT 
				vst_v.periodo || '00' as campo1,
				vst_v.periodo || vst_v.libro || vst_v.voucher as campo2,
				'M' || vst_v.voucher as campo3,
				TO_CHAR(vst_v.fecha_e :: DATE, 'dd/mm/yyyy') as campo4,
				CASE
					WHEN vst_v.td = '14' THEN TO_CHAR(vst_v.fecha_v :: DATE, 'dd/mm/yyyy')
					ELSE ''
				END AS campo5,
				CASE
					WHEN vst_v.td is not null THEN vst_v.td
					ELSE ''
				END AS campo6,
				CASE
					WHEN vst_v.serie is not null THEN vst_v.serie
					ELSE ''
				END AS campo7,
				CASE
					WHEN vst_v.numero is not null THEN vst_v.numero
					ELSE ''
				END AS campo8,
				CASE
					WHEN (am.campo_09_sale is not null) and (vst_v.td = '00' or vst_v.td = '03' or vst_v.td = '12' or vst_v.td = '13' or vst_v.td = '87') THEN am.campo_09_sale
					ELSE ''
				END AS campo9,
				CASE
					WHEN vst_v.tdp is not null THEN vst_v.tdp
					ELSE ''
				END AS campo10,
				CASE
					WHEN vst_v.docp is not null THEN vst_v.docp
					ELSE ''
				END AS campo11,
				CASE
					WHEN vst_v.namep is not null THEN vst_v.namep
					ELSE ''
				END AS campo12,
				CASE
					WHEN vst_v.exp is not null THEN vst_v.exp
					ELSE 0
				END AS campo13,
				CASE
					WHEN (am.is_descount is null or am.is_descount = False) and vst_v.venta_g is not null THEN vst_v.venta_g
					ELSE 0
				END AS campo14,
				CASE
					WHEN (am.is_descount = True) and vst_v.venta_g is not null THEN vst_v.venta_g
					ELSE 0
				END AS campo15,
				CASE
					WHEN (am.is_descount is null or am.is_descount = False) and vst_v.igv_v is not null THEN vst_v.igv_v
					ELSE 0
				END AS campo16,
				CASE
					WHEN (am.is_descount = True) and vst_v.igv_v is not null THEN vst_v.igv_v
					ELSE 0
				END AS campo17,
				CASE
					WHEN vst_v.exo is not null THEN vst_v.exo
					ELSE 0
				END AS campo18,
				CASE
					WHEN vst_v.inaf is not null THEN vst_v.inaf
					ELSE 0
				END AS campo19,
				CASE
					WHEN vst_v.isc_v is not null THEN vst_v.isc_v
					ELSE 0
				END AS campo20,
				0 as campo21,
				0 as campo22,
				CASE
					WHEN vst_v.otros_v is not null THEN vst_v.otros_v
					ELSE 0
				END AS campo23,
				CASE
					WHEN vst_v.total is not null THEN vst_v.total
					ELSE 0
				END AS campo24,
				vst_v.name AS campo25,
				vst_v.currency_rate::numeric(12,3) as campo26,
				CASE
					WHEN vst_v.f_doc_m is not null THEN TO_CHAR(vst_v.f_doc_m :: DATE, 'dd/mm/yyyy')
					ELSE ''
				END AS campo27,
				CASE
					WHEN vst_v.td_doc_m is not null THEN vst_v.td_doc_m
					ELSE ''
				END AS campo28,
				CASE
					WHEN vst_v.serie_m is not null THEN vst_v.serie_m
					ELSE ''
				END AS campo29,
				CASE
					WHEN vst_v.numero_m is not null THEN vst_v.numero_m
					ELSE ''
				END AS campo30,
				'' AS campo31,
				CASE
					WHEN am.campo_32_sale = True THEN '1'
					ELSE ''
				END AS campo32,
				CASE
					WHEN am.campo_33_sale = True THEN '1'
					ELSE ''
				END AS campo33,
				am.campo_34_sale AS campo34,
				'' AS campo35
				FROM vst_ventas_1_1 vst_v
				LEFT JOIN account_move am ON am.id = vst_v.am_id
				WHERE (vst_v.fecha_cont between '%s' and '%s')
				and vst_v.company = %s 
				ORDER BY vst_v.periodo, vst_v.libro, vst_v.voucher
			""" % (x_date_ini.strftime('%Y/%m/%d'),
					x_date_end.strftime('%Y/%m/%d'),
					str(x_company_id))

		return sql

	def _get_sql(self):

		sql = """select id, periodo, fecha_cont, libro, voucher, fecha_e, fecha_v, td, 
				serie, anio, numero, tdp, docp, namep, exp, venta_g, inaf, exo, isc_v, 
				otros_v, igv_v, total, name, monto_me, currency_rate, fecha_det, 
				comp_det, f_doc_m, td_doc_m, serie_m, numero_m, glosa
				from vst_ventas_1_1
				where (fecha_cont between '%s' and '%s')
				and company = %s 
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