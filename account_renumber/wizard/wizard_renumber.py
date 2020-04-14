# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import *

class WizardRenumber(models.TransientModel):
	_name = "wizard.renumber"

	def get_period(self):
		fiscal_year = self.env['main.parameter'].search([('company_id','=',self.env.company.id)],limit=1).fiscal_year
		if not fiscal_year:
			raise UserError(u'No se ha configurado un Año Fiscal en parametros generales de Contabilidad')
		else:
			today = date.today()
			period = self.env['account.period'].search([('fiscal_year_id', '=', fiscal_year.id),
											   ('date_start', '<=', today),
											   ('date_end', '>=', today)],limit=1)
			if not period:
				raise UserError('No se encontro Periodo para la Fecha Actual')
			else:
				return period

	period_id = fields.Many2one('account.period',string='Periodo',default=lambda self:self.get_period().id)
	journal_id = fields.Many2one('account.journal',string='Diario')

	@api.onchange('period_id')
	def onchange_fiscal_year(self):
		return {'domain':{'period_id':[('fiscal_year_id','=',self.get_period().fiscal_year_id.id)]}}

	def renumber(self):
		sequence = self.journal_id.sequence_id
		if not sequence:
			raise UserError('Es necesario que el Diario tenga una Secuencia')

		sql_where = """
			WHERE DATE BETWEEN '%s' AND '%s'
			AND JOURNAL_ID = %d
		""" % (self.period_id.date_start, self.period_id.date_end, self.journal_id.id)

		self.env.cr.execute(""" 
		update account_move set name =  '%s' || '-' || LPAD(T.CORRELATIVO::text,%s,'0')  
			from (
				SELECT row_number() OVER () AS CORRELATIVO,* FROM (
					SELECT  ID,DATE,NAME,REF,JOURNAL_ID FROM ACCOUNT_MOVE 
					%s
					ORDER BY DATE,LEFT(NAME,2)
				)TT
			) T where T.id = account_move.id
			""" % (self.period_id.code.split('/')[0], sequence.padding, sql_where))

		self.env.cr.execute("""
			select max(CORRELATIVO)+1 from (
				SELECT row_number() OVER () AS CORRELATIVO,* FROM (
					SELECT  ID,DATE,NAME,REF,JOURNAL_ID FROM ACCOUNT_MOVE 
					%s
					ORDER BY DATE,LEFT(NAME,2)
				)TT 
			) X
		 """ % (sql_where))

		res = self.env.cr.fetchall()

		default = 1
		for i in res:
			default = i[0]

		if sequence.use_date_range:
			date_range = self.env["ir.sequence.date_range"].search([("sequence_id", "=", sequence.id),
																	("date_from", "=", self.period_id.date_start),
																	("date_to", ">=", self.period_id.date_end)])
			if len(date_range)>1:
				raise UserError('Existe dos intervalos de fecha que se cruzan en el diario ' + self.journal_id.name)
			else:
				date_range[0].number_next_actual = default
				date_range[0].number_next = default
		else:
			sequence.number_next_actual = default

		self.env.cr.execute("""
			update account_payment set move_name = T.NAME,payment_reference = T.NAME  from (
				SELECT row_number() OVER () AS CORRELATIVO,* FROM (
					SELECT ap.ID,am.NAME FROM ACCOUNT_MOVE am
					INNER JOIN  ACCOUNT_MOVE_LINE aml on aml.move_id = am.id
					INNER JOIN account_payment ap on ap.id = aml.payment_id
					WHERE am.DATE BETWEEN '%s' AND '%s'
					AND am.JOURNAL_ID = %d
					ORDER BY am.DATE,LEFT(am.NAME,2)
				)TT
			) T where T.id = account_payment.id
		""" % (self.period_id.date_start, self.period_id.date_end, self.journal_id.id))

		self.env.cr.execute("""
			update account_bank_statement_line set move_name = T.NAME from (
				SELECT row_number() OVER () AS CORRELATIVO,* FROM (
					SELECT AML.STATEMENT_LINE_ID as ID,AM.DATE,AM.NAME,AM.REF,AM.JOURNAL_ID FROM ACCOUNT_MOVE AM
					INNER JOIN ACCOUNT_MOVE_LINE AML ON AML.MOVE_ID = AM.ID
					WHERE am.DATE BETWEEN '%s' AND '%s'
					AND am.JOURNAL_ID = %d
					ORDER BY am.DATE,LEFT(am.NAME,2)
				)TT
			) T where T.id = account_bank_statement_line.id
		""" % (self.period_id.date_start, self.period_id.date_end, self.journal_id.id))
		return self.env['popup.it'].get_message('SE GENERO EXITOSAMENTE')