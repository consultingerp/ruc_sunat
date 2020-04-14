# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCurrency(models.Model):
	_inherit = 'res.currency'

	def get_wizard(self):
		wizard = self.env['res.currency.wizard'].create({'name':'Actualizar T.C.'})
		return {
			'res_id':wizard.id,
			'view_mode':'form',
			'res_model':'res.currency.wizard',
			'views':[[self.env.ref('currency_rate_update.view_res_currency_wizard_form').id,'form']],
			'type':'ir.actions.act_window',
			'target':'new'
		}