# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'

	aux_currency_rate = fields.Float(default=1,digits=(16,4))

	@api.onchange('invoice_date','currency_id')
	def _get_currency_rate(self):
		if (self.type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund'] and self.currency_id.name == 'USD') or (self.type in ['entry']):
			if not self.tc_per:
				date_currency = self.invoice_date if self.invoice_date else fields.Date.today()
				cu_rate = self.env['res.currency.rate'].search([('name','=',date_currency)],limit=1)
				if cu_rate:
					self.currency_rate = cu_rate.sale_type
					self.aux_currency_rate = cu_rate.sale_type
		else:
			self.currency_rate = 1
			self.aux_currency_rate = 1
		
	@api.model
	def create(self,vals):
		if 'aux_currency_rate' in vals:
			vals.update({'currency_rate':vals['aux_currency_rate']})
		return super(AccountMove,self).create(vals)

	def write(self,vals):
		if 'aux_currency_rate' in vals:
			vals.update({'currency_rate':vals['aux_currency_rate']})
		return super(AccountMove,self).write(vals)

	def action_post(self):
		if self.currency_id.name != 'PEN':
			date_currency = self.invoice_date if self.invoice_date else fields.Date.today()
			if not self.env['res.currency.rate'].search([('name', '=', date_currency)]):
				raise UserError('No existe un tipo de cambio para la fecha de la factura')
		for line in self.line_ids:
			line.tc = self.currency_rate if line.currency_id.name == 'USD' else 1
		return super(AccountMove,self).action_post()