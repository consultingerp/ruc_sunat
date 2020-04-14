# -*- coding: utf-8 -*-

from collections import namedtuple
import json
import time
from odoo import api, fields, models, _ , exceptions


class type_operation_kardex(models.Model):
	_name = 'type.operation.kardex'

	name = fields.Char('Nombre')
	code = fields.Char('Codigo')


class PickingType(models.Model):
	_inherit = "stock.picking"


	kardex_date = fields.Datetime(string='Fecha kardex', readonly=False)
	use_kardex_date = fields.Boolean('Usar Fecha kardex',default=True)
	invoice_id = fields.Many2one('account.move','Factura',domain=[('type', 'in', ['out_invoice','in_invoice','out_refund','in_refund'])])
	type_operation_sunat_id = fields.Many2one('type.operation.kardex','Tipo de Operacion SUNAT')
	