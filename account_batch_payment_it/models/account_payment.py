# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccounthPayment(models.Model):
	_inherit = "account.payment"

	manual_batch_payment_id = fields.Many2one('account.batch.payment',string='Lote de Pago')

	@api.onchange('manual_batch_payment_id')
	def get_batch_data(self):
		self.cash_nro_comp = self.manual_batch_payment_id.name or ''
		self.journal_id = self.manual_batch_payment_id.journal_id or self.journal_id
		self.catalog_payment_id = self.manual_batch_payment_id.catalog_payment_id or self.catalog_payment_id