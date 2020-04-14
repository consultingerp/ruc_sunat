# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'

	@api.onchange('serie_id')
	def onchange_serie_id(self):
		if self.name == '/':
			if self.serie_id:
				next_number = self.serie_id.sequence_id.number_next_actual
				if not self.serie_id.sequence_id.prefix:
					raise UserError("No existe un prefijo configurado en la secuencia de la serie.")
				prefix = self.serie_id.sequence_id.prefix
				padding = self.serie_id.sequence_id.padding
				self.ref = prefix + "0"*(padding - len(str(next_number))) + str(next_number)

	def action_post(selfs):
		for self in selfs:
			if self.name == '/':
				if self.serie_id.sequence_id:
					next_number = self.serie_id.sequence_id.number_next_actual
					if not self.serie_id.sequence_id.prefix:
						raise UserError("No existe un prefijo configurado en la secuencia de la serie.")
					prefix = self.serie_id.sequence_id.prefix
					padding = self.serie_id.sequence_id.padding
					self.ref = prefix + "0"*(padding - len(str(next_number))) + str(next_number)
					self.serie_id.sequence_id.next_by_id()
			return super(AccountMove,self).action_post()
