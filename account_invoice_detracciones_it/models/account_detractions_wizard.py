# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountDetractionsWizard(models.TransientModel):
	_name = 'account.detractions.wizard'

	fecha = fields.Date(string='Fecha')
	monto = fields.Float(string='Monto',digits=(12,2))

	def generar(self):
		invoice = self.env['account.move'].search( [('id','=',self.env.context['invoice_id'])])[0]
		m = self.env['main.parameter'].search([('company_id','=',invoice.company_id.id)],limit=1)

		if not m.detraction_journal.id:
			raise UserError(u"No esta configurada el Diario de Detracción en Parametros Principales de Contabilidad para su Compañía")
		if not m.detractions_account.id:
			raise UserError(u"No esta configurada la Cuenta de Detracción para Proveedor en Parametros Principales de Contabilidad para su Compañía")

		flag_ver = True
		data = {
			'journal_id': m.detraction_journal.id,
			'ref':(invoice.name if invoice.name else 'Borrador'),
			'date': self.fecha,
			'company_id': invoice.company_id.id,
		}
		if invoice.name_move_detraccion and invoice.diario_move_detraccion.id == m.detraction_journal.id and invoice.fecha_move_detraccion == invoice.invoice_date:
			data['name']= invoice.name_move_detraccion
			flag_ver = False
		else:
			invoice.diario_move_detraccion= m.detraction_journal.id
			invoice.fecha_move_detraccion = invoice.invoice_date
			flag_ver = True
		lines = []

		if invoice.type == 'in_invoice':
			if invoice.currency_id.name == 'USD':
				line_cc = (0,0,{
					'account_id': invoice.partner_id.property_account_payable_id.id,
					'debit': self.monto * invoice.currency_rate,
					'credit':0,
					'name':'PROVISION DE LA DETRACCION',
					'partner_id': invoice.partner_id.id,
					'nro_comp': invoice.ref,
					'type_document_id': invoice.type_document_id.id,
					'amount_currency': self.monto,
					'tc': invoice.currency_rate,
					'company_id': invoice.company_id.id,			
					})
				lines.append(line_cc)

				line_cc = (0,0,{
					'account_id': m.detractions_account.id ,
					'debit': 0,
					'credit':self.monto * invoice.currency_rate,
					'name':'PROVISION DE LA DETRACCION',
					'partner_id': invoice.partner_id.id,
					'nro_comp': invoice.ref,
					'type_document_id': invoice.type_document_id.id,
					'company_id': invoice.company_id.id,	
					})
				lines.append(line_cc)

			else:
				line_cc = (0,0,{
					'account_id': invoice.partner_id.property_account_payable_id.id,
					'debit': self.monto,
					'credit':0,
					'name':'PROVISION DE LA DETRACCION',
					'partner_id': invoice.partner_id.id,
					'nro_comp': invoice.ref,
					'type_document_id': invoice.type_document_id.id,
					'company_id': invoice.company_id.id,	
					})
				lines.append(line_cc)

				line_cc = (0,0,{
					'account_id': m.detractions_account.id ,
					'debit': 0,
					'credit':self.monto,
					'name':'PROVISION DE LA DETRACCION',
					'partner_id': invoice.partner_id.id,
					'nro_comp': invoice.ref,
					'type_document_id': invoice.type_document_id.id,
					'company_id': invoice.company_id.id,	
					})
				lines.append(line_cc)

		if invoice.type == 'out_invoice':
			if invoice.currency_id.name == 'USD':
				line_cc = (0,0,{
					'account_id': m.detractions_account.id ,
					'debit': self.monto * invoice.currency_rate,
					'credit':0,
					'name':'PROVISION DE LA DETRACCION',
					'partner_id': invoice.partner_id.id,
					'nro_comp': invoice.ref,
					'type_document_id': invoice.type_document_id.id,
					'amount_currency': self.monto,
					'tc': invoice.currency_rate,
					'company_id': invoice.company_id.id,			
					})
				lines.append(line_cc)

				line_cc = (0,0,{
					'account_id': invoice.partner_id.property_account_receivable_id.id,
					'debit': 0,
					'credit':self.monto * invoice.currency_rate,
					'name':'PROVISION DE LA DETRACCION',
					'partner_id': invoice.partner_id.id,
					'nro_comp': invoice.ref,
					'type_document_id': invoice.type_document_id.id,
					'company_id': invoice.company_id.id,	
					})
				lines.append(line_cc)

			else:
				line_cc = (0,0,{
					'account_id': m.detractions_account.id ,
					'debit': self.monto,
					'credit':0,
					'name':'PROVISION DE LA DETRACCION',
					'partner_id': invoice.partner_id.id,
					'nro_comp': invoice.ref,
					'type_document_id': invoice.type_document_id.id,
					'company_id': invoice.company_id.id,	
					})
				lines.append(line_cc)

				line_cc = (0,0,{
					'account_id': invoice.partner_id.property_account_receivable_id.id,
					'debit': 0,
					'credit':self.monto,
					'name':'PROVISION DE LA DETRACCION',
					'partner_id': invoice.partner_id.id,
					'nro_comp': invoice.ref,
					'type_document_id': invoice.type_document_id.id,
					'company_id': invoice.company_id.id,	
					})
				lines.append(line_cc)

		data['line_ids'] = lines
		tt = self.env['account.move'].create(data)
		if tt.state =='draft':
			tt.post()
		invoice.move_detraccion_id = tt.id

		if flag_ver:
			invoice.name_move_detraccion = tt.name

		return True