# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Einvoice(models.Model):
	_name = 'einvoice'

	move_id = fields.Many2one('account.move',ondelete='cascade')
	related_ref = fields.Char(related='move_id.ref',string='Referencia',store=True)
	total_saved = fields.Float(string='Total Grabado',digits=(12,2))
	total_inafect = fields.Float(string='Total Inafecto',digits=(12,2))
	total_exonerate = fields.Float(string='Total Exonerado',digits=(12,2))
	total_free = fields.Float(string='Total Gratuito',digits=(12,2))
	total_another_charges = fields.Float(string='Total Otros Cargos',digits=(12,2))
	global_discount = fields.Float(string='Descuento Global',digits=(12,2))
	total_discount = fields.Float(string='Descuento Total',digits=(12,2))
	total_advance = fields.Float(string='Total Anticipo',digits=(12,2))
	total_igv = fields.Float(string='Total IGV',digits=(12,2))
	total_icbper = fields.Float(string='Total ICBPER',digits=(12,2))
	total_voucher = fields.Float(string='Total Comprobante',digits=(12,2))
	perception_type = fields.Char(string='Tipo Percepcion',size=2)
	perception_tax_base = fields.Float(string='Percepcion Base Imponible',digits=(12,2))
	total_perception = fields.Float(string='Total Percepcion',digits=(12,2))
	total_included_perception = fields.Float(string='Total Incluido Percepcion',digits=(12,2))
	have_detraction = fields.Boolean(string='Tiene Detraccion',default=False)