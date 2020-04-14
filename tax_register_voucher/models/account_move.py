# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'

	personalize_tax = fields.Boolean(string="Impuesto Personalizado",default=False)

	def action_post(self):
		if self.type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund']:
			for line in self.line_ids:
				if not self.personalize_tax:
					if len(line.tag_ids.ids) > 0:
						line.tax_amount_it = -line.credit if line.credit > 0 else line.debit
		return super(AccountMove,self).action_post()