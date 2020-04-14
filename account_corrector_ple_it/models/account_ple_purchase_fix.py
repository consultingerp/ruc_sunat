# -- coding: utf-8 --

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountPlePurchaseFix(models.Model):
	_name = 'account.ple.purchase.fix'

	@api.depends('period_id')
	def _get_name(self):
		for i in self:
			i.name = i.period_id.code

	name = fields.Char(compute=_get_name,store=True)
	period_id = fields.Many2one('account.period',string='Periodo',required=True)
	annulled = fields.One2many('fix.line.purchase.annulled','fix_id',string='Anulados')
	state_document = fields.One2many('fix.line.purchase.state','fix_id',string='Estado Documento')
	acquisition = fields.One2many('fix.line.purchase.acquisition','fix_id',string=u'Adquisición')
	date = fields.One2many('fix.line.purchase.date','fix_id',string='Fecha')

	badly_annulled = fields.Integer(string='Por Corregir Anulados')
	badly_state_document = fields.Integer(string='Por Corregir Estado Documento')
	badly_acquisition = fields.Integer(string=u'Por Corregir Adquisición')
	badly_date = fields.Integer(string='Por Corregir Fecha')

	acquisition_check = fields.Boolean(string=u'Mantener Tipo de Adquisición',default=True)
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=1)

	def _get_sql_annulled(self,libro_id,estado):
		parametros = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)

		if not parametros.cancelation_partner:
			raise UserError(u"Debe elegir un Partner para anulaciones en Parametros Principales de Contabilidad para la Compañía")

		sql_annulled = """SELECT id FROM account_move
							WHERE state = 'posted' 
							AND journal_id = %s 
							AND (date between '%s' and '%s') 
							AND partner_id = %s
							AND campo_41_purchase != '%s'
							""" % (str(libro_id),
							self.period_id.date_start.strftime('%Y/%m/%d'),
							self.period_id.date_end.strftime('%Y/%m/%d'),
							str(parametros.cancelation_partner.id),
							estado)
		return sql_annulled

	def _get_sql_acquisition(self,libro_id):
		sql_acquisition = """SELECT aa.type_adquisition, aml.move_id FROM account_move_line aml
							LEFT JOIN account_account aa ON aa.id = aml.account_id
							WHERE aml.id in (SELECT min(aml.id) as aml_id FROM account_move am
								LEFT JOIN account_move_line aml on aml.move_id = am.id
								LEFT JOIN account_account aa on aml.account_id = aa.id
								WHERE am.state = 'posted'
								and am.journal_id = %s
								and (am.date between '%s' and '%s')
								and aa.type_adquisition != am.campo_34_purchase
								group by am.id)
							""" % (str(libro_id),
							self.period_id.date_start.strftime('%Y/%m/%d'),
							self.period_id.date_end.strftime('%Y/%m/%d'))
		return sql_acquisition

	def _get_sql_state_document(self,libro_id,documento_id,estado):
		sql_state_document = """SELECT id FROM account_move
								WHERE state = 'posted'
								and journal_id = %s
								and (date between '%s' and '%s')
								and type_document_id = %s
								and campo_41_purchase != '%s'
								""" % (str(libro_id),
								self.period_id.date_start.strftime('%Y/%m/%d'),
								self.period_id.date_end.strftime('%Y/%m/%d'),
								str(documento_id),
								estado)
		return sql_state_document

	def _get_sql_date(self,libro_id,documento_id,estado):
		sql_date = "and invoice_date < '%s'" % (self.period_id.date_start.strftime('%Y/%m/%d'))
		if estado == '6':
			sql_date = "and (invoice_date between date - interval '1 year' and '%s'::date - interval '1 day')" % (self.period_id.date_start.strftime('%Y/%m/%d'))
		if estado == '7':
			sql_date = "and invoice_date < date - interval '1 year'"

		sql_date = """SELECT id FROM account_move
						WHERE state = 'posted'
						and journal_id = %s
						and (date between '%s' and '%s')
						and type_document_id = %s
						%s
						and campo_41_purchase != '%s'
						""" % (str(libro_id),
						self.period_id.date_start.strftime('%Y/%m/%d'),
						self.period_id.date_end.strftime('%Y/%m/%d'),
						str(documento_id),
						sql_date,
						estado)

	def calculate(self):
		########################################################### POR CORREGIR ANULADOS #########################################################
		conta= 0
		for i in self.annulled:
			self.env.cr.execute(self._get_sql_annulled(i.libro.id,i.estado))
			conta += len(self.env.cr.fetchall())

		self.badly_annulled = conta

		########################################################### POR CORREGIR ADQUISICION #########################################################
		conta = 0
		for i in self.acquisition:
			self.env.cr.execute(self._get_sql_acquisition(i.libro.id))
			conta += len(self.env.cr.fetchall())

		self.badly_acquisition = conta

		########################################################### POR CORREGIR ESTADO DOCUMENTO #########################################################
		conta = 0
		for i in self.state_document:
			self.env.cr.execute(self._get_sql_state_document(i.libro.id,i.documento.id,i.estado))
			conta += len(self.env.cr.fetchall())

		self.badly_state_document = conta

		########################################################### POR CORREGIR FECHA #########################################################
		conta = 0

		for i in self.date:
			self.env.cr.execute(self._get_sql_date(i.libro.id,i.documento.id,i.estado))
			conta += len(self.env.cr.fetchall())

		self.badly_date = conta


	def fix(self):
		self.fix_annulled()
		self.fix_acquisition()
		self.fix_state_document()
		self.fix_date()
		self.calculate()

	def fix_annulled(self):
		for i in self.annulled:
			sql_update = """UPDATE account_move 
							SET campo_41_purchase = '%s'
							WHERE id in (%s)
							""" % (i.estado,
								self._get_sql_annulled(i.libro.id,i.estado))
			self.env.cr.execute(sql_update)

	def fix_acquisition(self):
		for i in self.acquisition:
			self.env.cr.execute(self._get_sql_acquisition(i.libro.id))
			res = self.env.cr.fetchall()
			for j in res:
				sql_update = """UPDATE account_move
								SET campo_34_purchase = '%s'
								WHERE id = %s
								""" % (j[0],j[1])
				self.env.cr.execute(sql_update)

	def fix_state_document(self):
		for i in self.state_document:
			sql_update = """UPDATE account_move
							SET campo_41_purchase = '%s'
							WHERE id in (%s)
							""" % (i.estado,
								self._get_sql_state_document(i.libro.id,i.documento.id,i.estado))
			self.env.cr.execute(sql_update)

	def fix_date(self):
		for i in self.date:
			sql_update = """UPDATE account_move
							SET campo_41_purchase = '%s'
							WHERE id in (%s)
							""" % (i.estado,
								self._get_sql_date(i.libro.id,i.documento.id,i.estado))

			self.env.cr.execute(sql_update)

class FixLinePurchaseAnnulled(models.Model):
	_name = 'fix.line.purchase.annulled'

	fix_id = fields.Many2one('account.ple.purchase.fix',string='Corrector')
	libro = fields.Many2one('account.journal',string='Libro')
	estado = fields.Char(string='Estado')
	

class FixLinePurchaseState(models.Model):
	_name = 'fix.line.purchase.state'

	fix_id = fields.Many2one('account.ple.purchase.fix',string='Corrector')
	documento = fields.Many2one('einvoice.catalog.01',string='Tipo Documento')
	libro = fields.Many2one('account.journal',string='Libro')
	estado = fields.Char(string='Estado')


class FixLinePurchaseAcquisition(models.Model):
	_name = 'fix.line.purchase.acquisition'

	fix_id = fields.Many2one('account.ple.purchase.fix',string='Corrector')
	libro = fields.Many2one('account.journal',string='Libro')


class FixLinePurchaseDate(models.Model):
	_name = 'fix.line.purchase.date'

	fix_id = fields.Many2one('account.ple.purchase.fix',string='Corrector')
	documento = fields.Many2one('einvoice.catalog.01',string='Tipo Documento')
	libro = fields.Many2one('account.journal',string='Libro')
	estado = fields.Char(string='Estado')