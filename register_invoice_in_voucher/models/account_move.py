# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountMove(models.Model):
	_inherit = 'account.move'

	def action_post(self):
		if self.type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund']:
			for line in self.line_ids:
				line.tc = self.currency_rate if line.currency_id.name == 'USD' else 1
				line.type_document_id = self.type_document_id.id or None
				line.nro_comp = self.ref or None
		return super(AccountMove,self).action_post()