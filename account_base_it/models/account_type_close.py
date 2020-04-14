# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountTypeClose(models.Model):
	_name = 'account.type.close'

	period_id = fields.Many2one('account.period',string='Periodo')
	type_purchase = fields.Float(string='Tipo de Compra',digits=(12,3))
	type_sale = fields.Float(string='Tipo de Venta',digits=(12,3))