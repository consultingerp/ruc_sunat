# -- coding: utf-8 --

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountPleSaleFix(models.Model):
	_name = 'account.ple.sale.fix'

	@api.depends('period_id')
	def _get_name(self):
		for i in self:
			i.name = i.period_id.code

	name = fields.Char(compute=_get_name,store=True)
	period_id = fields.Many2one('account.period',string='Periodo',required=True)
	annulled = fields.One2many('fix.line.sale.annulled','fix_id',string='Anulados')
	state_document = fields.One2many('fix.line.sale.state','fix_id',string='Estado Documento')
	date = fields.One2many('fix.line.sale.date','fix_id',string='Fecha')

	badly_annulled = fields.Integer(string='Por Corregir Anulados')
	badly_state_document = fields.Integer(string='Por Corregir Estado Documento')
	badly_date = fields.Integer(string='Por Corregir Fecha')

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
							AND campo_34_sale != '%s'
							""" % (str(libro_id),
							self.period_id.date_start.strftime('%Y/%m/%d'),
							self.period_id.date_end.strftime('%Y/%m/%d'),
							str(parametros.cancelation_partner.id),
							estado)
		return sql_annulled

	def _get_sql_state_document(self,libro_id,documento_id,estado):
		sql_state_document = """SELECT id FROM account_move
								WHERE state = 'posted'
								and journal_id = %s
								and (date between '%s' and '%s')
								and type_document_id = %s
								and campo_34_sale != '%s'
								""" % (str(libro_id),
								self.period_id.date_start.strftime('%Y/%m/%d'),
								self.period_id.date_end.strftime('%Y/%m/%d'),
								str(documento_id),
								estado)
		return sql_state_document

	def _get_sql_date(self,libro_id,documento_id,estado):
		sql_date = """SELECT id FROM account_move
						WHERE state = 'posted'
						and journal_id = %s
						and (date between '%s' and '%s')
						and type_document_id = %s
						and invoice_date < '%s'
						and campo_34_sale != '%s'
						""" % (str(libro_id),
						self.period_id.date_start.strftime('%Y/%m/%d'),
						self.period_id.date_end.strftime('%Y/%m/%d'),
						str(documento_id),
						self.period_id.date_start.strftime('%Y/%m/%d'),
						estado)

	def calculate(self):
		########################################################### POR CORREGIR ANULADOS #########################################################
		conta= 0
		for i in self.annulled:
			self.env.cr.execute(self._get_sql_annulled(i.libro.id,i.estado))
			conta += len(self.env.cr.fetchall())

		self.badly_annulled = conta

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
		self.fix_state_document()
		self.fix_date()
		self.calculate()

	def fix_annulled(self):
		for i in self.annulled:
			sql_update = """UPDATE account_move 
							SET campo_34_sale = '%s'
							WHERE id in (%s)
							""" % (i.estado,
								self._get_sql_annulled(i.libro.id,i.estado))
			print(sql_update)
			#self.env.cr.execute(sql_update)

	def fix_state_document(self):
		for i in self.state_document:
			sql_update = """UPDATE account_move
							SET campo_34_sale = '%s'
							WHERE id in (%s)
							""" % (i.estado,
								self._get_sql_state_document(i.libro.id,i.documento.id,i.estado))
			print(sql_update)
			#self.env.cr.execute(sql_update)

	def fix_date(self):
		for i in self.date:
			sql_update = """UPDATE account_move
							SET campo_34_sale = '%s'
							WHERE id in (%s)
							""" % (i.estado,
								self._get_sql_date(i.libro.id,i.documento.id,i.estado))

			print(sql_update)
			#self.env.cr.execute(sql_update)

class FixLineSaleAnnulled(models.Model):
	_name = 'fix.line.sale.annulled'

	fix_id = fields.Many2one('account.ple.sale.fix',string='Corrector')
	libro = fields.Many2one('account.journal',string='Libro')
	estado = fields.Char(string='Estado')
	

class FixLineSaleState(models.Model):
	_name = 'fix.line.sale.state'

	fix_id = fields.Many2one('account.ple.sale.fix',string='Corrector')
	documento = fields.Many2one('einvoice.catalog.01',string='Tipo Documento')
	libro = fields.Many2one('account.journal',string='Libro')
	estado = fields.Char(string='Estado')


class FixLineSaleDate(models.Model):
	_name = 'fix.line.sale.date'

	fix_id = fields.Many2one('account.ple.sale.fix',string='Corrector')
	documento = fields.Many2one('einvoice.catalog.01',string='Tipo Documento')
	libro = fields.Many2one('account.journal',string='Libro')
	estado = fields.Char(string='Estado')