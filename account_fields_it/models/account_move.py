# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang, format_date, get_lang


class AccountMove(models.Model):
	_inherit = 'account.move'

	td_payment_id = fields.Many2one('einvoice.catalog.payment',string='Medio de Pago')
	ple_state = fields.Selection([('1','Fecha del Comprobante Corresponde al Periodo'),
								('8','Corresponde a un Periodo Anterior y no ha sido Anotado en dicho Periodo'),
								('9','Corresponde a un Periodo Anterior y si ha sido Anotado en dicho Periodo')],string='Estado para el PLE', default='1')
	date_corre_ple = fields.Date(string='Fecha Correccion PLE')
	type_document_id = fields.Many2one('einvoice.catalog.01',string='Tipo de Documento')
	ref = fields.Char(string='Reference', copy=False)
	serie_id = fields.Many2one('it.invoice.serie',string='Serie')
	currency_rate = fields.Float(string='Tipo de Cambio',digits=(16,4),readonly=True,default=1)
	tc_per = fields.Boolean(string='Usar Tc Personalizado',default=False)
	glosa = fields.Char(string='Glosa')
	is_opening_close = fields.Boolean(string=u'Apertura/Cierre',default=False)
	perception_date = fields.Date(string='Fecha Uso Percepcion')
	es_editable = fields.Boolean('Es editable',related='journal_id.voucher_edit')
	is_descount = fields.Boolean(string=u'Es descuento', default=False)

	#Pestaña: SUNAT
	date_detraccion = fields.Date(string='Fecha')
	code_operation = fields.Char(string='Codigo de Operacion',size=2)
	voucher_number = fields.Char(string='Numero de Comprobante')
	detra_amount = fields.Float(string='Monto',digits=(16, 2))
	type_t_perception = fields.Char(string='Tipo Tasa Percepcion',size=3)
	number_perception = fields.Char(string='Numero Percepcion',size=6)
	delivery_id = fields.Many2one('account.delivery',string='Nro. Entrega')
	petty_cash_id = fields.Many2one('account.petty.cash',string='Nro. Caja')
	switch = fields.Boolean(string='Actualizar', default=False)

	automatic_destiny = fields.Boolean(string='Destino automatico',default=False)

	@api.onchange('type')
	def domain_partner(self):
		if self.type in ['in_invoice','in_refund','in_receipt']:
			domain = [('supplier_rank','>',0)]
			res = {'domain': {'partner_id': domain}}
			return res
		if self.type in ['out_invoice','out_refund','out_receipt']:
			domain = [('customer_rank','>',0)]
			res = {'domain': {'partner_id': domain}}
			return res

	@api.onchange('ref','type_document_id')
	def _get_ref(self):
		if self.type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund']:
			digits_serie = ('').join(self.type_document_id.digits_serie*['0'])
			digits_number = ('').join(self.type_document_id.digits_number*['0'])
			if self.ref:
				if '-' in self.ref:
					partition = self.ref.split('-')
					if len(partition) == 2:
						serie = digits_serie[:-len(partition[0])] + partition[0]
						number = digits_number[:-len(partition[1])] + partition[1]
						self.ref = serie + '-' + number
					else:
						raise UserError('El formato del Nro. Comprobante es incorrecto')

	def action_change_name(self):
		for move in self:
			if move.state == 'draft':
				move.name = "/"
				return self.env['popup.it'].get_message('Se borro correctamente la secuencia.')
			else:
				raise UserError("No puede alterar el nombre si no se encuentra en estado Borrador")

	def action_change_line(self):
		if self.type not in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund']:
			sql = """update account_move_line set debit = 1 where move_id = """+str(self.id)+""" and credit = 0 and debit = 0 """
			self.env.cr.execute(sql)
			return self.env['popup.it'].get_message('Se actualizaron correctamente las lineas.')
		else:
			raise UserError("No es un asiento")
		

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	type_document_id = fields.Many2one('einvoice.catalog.01',string='T.D.')
	nro_comp = fields.Char(string='Nro Comp.',size=40)
	tc = fields.Float(string='T.C.',digits=(12,4),default=1)
	cash_flow_id = fields.Many2one('account.cash.flow',string="Flujo Caja")
	tax_amount_it = fields.Monetary(default=0.0, currency_field='company_currency_id',string='Importe Imp.')
	cuo = fields.Integer(string="CUO")

	@api.onchange('nro_comp','type_document_id')
	def _get_ref(self):
		digits_serie = ('').join(self.type_document_id.digits_serie*['0'])
		digits_number = ('').join(self.type_document_id.digits_number*['0'])
		if self.nro_comp:
			if '-' in self.nro_comp:
				partition = self.nro_comp.split('-')
				if len(partition) == 2:
					serie = digits_serie[:-len(partition[0])] + partition[0]
					number = digits_number[:-len(partition[1])] + partition[1]
					self.nro_comp = serie + '-' + number
				else:
					raise UserError('El formato del Nro. Comprobante es incorrecto')