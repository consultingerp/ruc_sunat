# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountJournal(models.Model):
	_inherit = 'account.journal'

	register_sunat = fields.Selection([('1','Compras'),
								('2','Ventas'),
								('3','Honorarios'),
								('4','Retenciones'),
								('5','Percepciones'),
								('6','No Deducibles')],string='Registro Sunat')
	voucher_edit = fields.Boolean(string=u'Editar Asiento', default=False)
	check_surrender = fields.Boolean(string=u'Diario de Rendición',default=False)