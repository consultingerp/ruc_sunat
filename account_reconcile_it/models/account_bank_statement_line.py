# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountBankStatementLine(models.Model):
	_inherit = 'account.bank.statement.line'

	def _prepare_reconciliation_move_line(self, move, amount):
		aml_dict = super(AccountBankStatementLine,self)._prepare_reconciliation_move_line(move, amount)
		aml_dict['nro_comp'] = self.ref or ''
		return aml_dict