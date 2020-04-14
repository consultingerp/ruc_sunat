# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountBankStatementLine(models.Model):
	_inherit = 'account.bank.statement.line'

	catalog_payment_id = fields.Many2one('einvoice.catalog.payment',string='Medio de Pago')
	
class AccountBankStatement(models.Model):
	_inherit = 'account.bank.statement'

	journal_check_surrender = fields.Boolean(string='Para rendiciones',related='journal_id.check_surrender',default=False,store=True)