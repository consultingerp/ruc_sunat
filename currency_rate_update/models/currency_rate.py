# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResCurrencyRate(models.Model):
	_inherit = 'res.currency.rate'

	purchase_type = fields.Float(string='Tipo Compra',digits=(16, 3))
	sale_type = fields.Float(string='Tipo Venta',digits=(16, 3))

	@api.onchange('sale_type')
	def _update_currency(self):
		for i in self:
			if i.sale_type:
				i.rate = 1/i.sale_type