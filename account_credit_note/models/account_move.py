# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'

	def replace_lines_fr(selfs):
		for self in selfs:
			lines = self.doc_invoice_relac
			if lines and len(lines) == 1:
				filtered_line = self.line_ids.filtered(lambda l: l.account_id.internal_type in ['receivable','payable'])
				filtered_line.type_document_id = lines[0].type_document_id
				filtered_line.nro_comp = lines[0].nro_comprobante
			else:
				raise UserError('No hay lineas de Documentos Relacionados o Existe mas de una Linea por lo que debera ejecutar este proceso de manera manual en el documento %s' % self.name)