# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'

	def action_post(selfs):
		for self in selfs:
			for line in self.line_ids:
				if self.currency_id.name != 'PEN' and line.account_id.user_type_id.type in ['receivable','payable'] and line.account_id.currency_id != self.currency_id:
					raise UserError('No se puede crear una Factura con moneda extranjera sin cuentas con moneda extranjera')
			return super(AccountMove,self).action_post()