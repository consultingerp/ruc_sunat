# -*- coding: utf-8 -*-

from odoo import models, fields, api

class F2Balance(models.Model):
	_name = 'f2.balance'
	_auto = False
	_order = 'mayor'

	mayor = fields.Char(string='Mayor')
	nomenclatura = fields.Char(string='Nomenclatura')
	debe_inicial = fields.Float(string='Debe Inicial')
	haber_inicial = fields.Float(string='Haber Inicial')
	debe = fields.Float(string='Debe')
	haber = fields.Float(string='Haber')
	saldo_deudor = fields.Float(string='Saldo Deudor')
	saldo_acreedor = fields.Float(string='Saldo Acreedor')
	activo = fields.Float(string='Activo')
	pasivo = fields.Float(string='Pasivo')
	perdinat = fields.Float(string='Perdinat')
	ganannat = fields.Float(string='Ganannat')
	perdifun = fields.Float(string='Perdifun')
	gananfun = fields.Float(string='Gananfun')