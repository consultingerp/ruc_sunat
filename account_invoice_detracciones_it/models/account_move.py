# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
	_inherit = 'account.move'

	name_move_detraccion = fields.Char(string=u'Nombre Detracción')
	diario_move_detraccion = fields.Many2one('account.journal',string=u'Nombre Diario')
	fecha_move_detraccion = fields.Date(string='Periodo')

	def get_state_button_detraction(self):
		for i in self:
			if i.state == 'posted' or i.invoice_payment_state == 'paid':
				if i.move_detraccion_id.id:
					i.state_detraction_button = 1
				else:
					i.state_detraction_button = 2
			else:
				i.state_detraction_button = 3

	move_detraccion_id = fields.Many2one('account.move',string=u'Asiento Detracción',copy=False)
	state_detraction_button = fields.Integer(string='Estado Boton', default=3,compute=get_state_button_detraction)

	def button_cancel(self):

		#vals_data = {}
		#ids_conciliar = []
		#for i1 in self.move_detraccion_id.line_ids:
		#	if i1.debit >0:
		#		ids_conciliar.append(i1.id)
		#"""
		#for i2 in self.move_id.line_id:
		#	if i2.account_id.id == self.account_id.id:
		#		ids_conciliar.append(i2.id)
		#"""
		#concile_move = self.with_context({'active_ids':ids_conciliar}).env['account.unreconcile'].create(vals_data)
		#concile_move.trans_unrec()


		if self.move_detraccion_id.id:
			if self.move_detraccion_id.state != 'draft':
				self.move_detraccion_id.button_cancel()
			self.move_detraccion_id.line_ids.unlink()
			self.move_detraccion_id.name = "/"
			self.move_detraccion_id.unlink()
		return super(AccountMove,self).button_cancel()

	def remove_detraccion_gastos(self):

		#vals_data = {}
		#ids_conciliar = []
		#for i1 in self.move_detraccion_id.line_ids:
		#	if i1.debit >0:
		#		ids_conciliar.append(i1.id)
		#"""
		#for i2 in self.move_id.line_id:
		#	if i2.account_id.id == self.account_id.id:
		#		ids_conciliar.append(i2.id)
		#"""
		#concile_move = self.with_context({'active_ids':ids_conciliar}).env['account.unreconcile'].create(vals_data)
		#concile_move.trans_unrec()


		if self.move_detraccion_id.id:
			if self.move_detraccion_id.state != 'draft':
				self.move_detraccion_id.button_cancel()
			self.move_detraccion_id.line_ids.unlink()
			self.move_detraccion_id.name = "/"
			self.move_detraccion_id.unlink()
		return True

	def create_detraccion_gastos(self):
		context = {'invoice_id': self.id,'default_fecha': self.invoice_date ,
		'default_monto':self.amount_total * float(self.partner_id.p_detraction)/100.0}
		return {
				'type': 'ir.actions.act_window',
				'name': "Generar Detracción",
				'view_type': 'form',
				'view_mode': 'form',
				'context': context,
				'res_model': 'account.detractions.wizard',
				'target': 'new',
		}
