# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang, format_date, get_lang


class AccountMove(models.Model):
	_inherit = 'account.move'


	currency_rate = fields.Float(string='Tipo de Cambio',digits=(16,4),readonly=False,default=1)
	tc_per = fields.Boolean(string='Usar Tc Personalizado',default=False)

	def generar_tipo_cambio(self):
		if not self.tc_per:
			raise UserError('No hay tipo de cambio personalizado.')

		for move in self:
			#Se actualizan las lineas de tipo de cambio
			self.env.cr.execute(""" 
				update account_move_line set debit = round((case when amount_currency >0 then amount_currency else 0 end ) *"""+str(self.currency_rate)+""",2) , credit = round((case when amount_currency <0 then -amount_currency else 0 end ) * """+str(self.currency_rate)+""",2),
				tc = """+str(self.currency_rate)+"""
				where move_id = """+str(self.id)+"""
				""")
			self.env.cr.execute(""" 
				update account_move_line set balance = debit - credit, amount_residual = debit-credit, tax_amount_it = debit-credit
				where move_id = """+str(self.id)+"""
				""")

			#Se revisa el descuadre
			self.env.cr.execute(""" select sum(debit-credit) from account_move_line where move_id = """+str(self.id)+""" ; """)
			descuadre = self.env.cr.fetchall()[0][0]

			if descuadre!= 0:
				parametros = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)

				if not parametros.supplier_advance_account_fc:
					raise UserError(u'No existe una Cuenta Anticipo Proveedor M.E. configurado en Parametros Principales de Contabilidad para su Compañía')

				if not parametros.supplier_advance_account_nc:
					raise UserError(u'No existe una Cuenta Anticipo Proveedor M.N. configurado en Parametros Principales de Contabilidad para su Compañía')

				cuenta = parametros.supplier_advance_account_fc.id if descuadre >0 else parametros.supplier_advance_account_nc.id
				self.env.cr.execute("""
					insert into account_move_line (move_id, move_name, date, journal_id, company_id,company_currency_id, account_id, name, debit,credit)
					values ("""+str(self.id)+""",'"""+str(self.name)+"""',"""+str(self.line_ids[0].date)+""","""+str(self.line_ids[0].journal_id.id)+""","""+str(self.line_ids[0].company_id.id)+""","""+str(self.line_ids[0].company_currency_id.id)+""","""+str(cuenta)+""",
					'"""+str('Redondeo')+"""',"""+str(descuadre if descuadre >0 else 0)+""","""+str(-descuadre if descuadre <0 else 0)+""",)

					""")

		return self.env['popup.it'].get_message('Se genero el tipo de cambio personalizado.')

	def _check_balanced(self):
		for i in self:
			if i.state != 'draft':
				super(AccountMove,i)._check_balanced()

	def write(self, vals):
		t = super(AccountMove,self).write(vals)
		self._check_balanced()
		return t

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	tc = fields.Float(string='T.C.',digits=(12,4),default=1)
