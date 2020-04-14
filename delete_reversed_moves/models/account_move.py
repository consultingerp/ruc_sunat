# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountMove(models.Model):
	_inherit = 'account.move'

	def _reverse_moves(self, default_values_list=None, cancel=False):
		t = super(AccountMove,self)._reverse_moves(default_values_list,cancel)
		flag = False
		for c,val in enumerate(default_values_list):
			if 'journal_id' not in val:
				flag = True
		if flag:
			sql = """
				delete
				from account_partial_reconcile
				where debit_move_id in (select id from account_move_line where move_id = {move_id})
				or credit_move_id in (select id from account_move_line where move_id = {move_id})
			""".format(move_id = t.id)
			self._cr.execute(sql)
			self._cr.execute("""delete from account_move where id = %d""" % t.id)
		return t