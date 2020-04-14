# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError

class ResCurrencyWizard(models.TransientModel):
	_name = 'res.currency.wizard'

	name = fields.Char()
	entity = fields.Selection([
							('0','SUNAT'),
							('1','SERVICIO NO DISPONIBLE')
							],string="Entidad",default='0')
	date_from = fields.Date(string='Fecha Inicio',default=lambda self:date.today())
	date_to = fields.Date(string='Fecha Fin',default=lambda self:date.today())

	@api.constrains('date_from','date_to')
	def _check_dates(selfs):
		for self in selfs:
			if self.date_from.month != self.date_to.month:
				raise UserError('La fecha de Inicio y Fin no pueden ser de meses distintos')
			if self.date_from > self.date_to:
				raise UserError('La fecha de Inicio no puede ser mayor a la fecha Fin')

	def verify_entity(self):
		if self.entity == '0':
			self.get_tc_sunat()

		return {
			'domain' : [('currency_id.name','=', 'USD')],
			'type': 'ir.actions.act_window',
			'res_model': 'res.currency.rate',
			'view_mode': 'tree',
			'view_type': 'form',
		}

	def get_tc_sunat(self):
		def date_range(date1, date2):
			for n in range(int ((date2 - date1).days + 1)):
				yield date1 + timedelta(n)

		def recursive_rate_call(dt):
			currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
			rates = currency.rate_ids
			rate = rates.filtered(lambda rate: rate.name == dt - timedelta(days = 1))
			if rate:
				return rate
			else:
				return recursive_rate_call(dt - timedelta(days = 1))

		from bs4 import BeautifulSoup
		import urllib3
		from urllib.parse import urlencode

		datos = urlencode({'mes':self.date_from.month, 'anho':self.date_from.year})
		url = "http://www.sunat.gob.pe/cl-at-ittipcam/tcS01Alias?"
		try:
			http = urllib3.PoolManager()
			response = http.request('GET',url + datos)
		except:
			raise UserError('No se puede conectar a la página de Sunat!')
		soup = BeautifulSoup(response.data)
		trs = soup.findAll('table')[1].findAll('tr')
		tcs = []
		trs.pop(0)
		for tr in trs:
			tds = tr.findAll('td')
			c, tc = 0, {}
			for td in tds:
				if c == 0:
					tc['day'] = int(td.text)
				if c == 1:
					tc['purchase_type'] = float(td.text)
				if c == 2:
					tc['sale_type'] = float(td.text)
					tc['rate'] = 1 / float(td.text)
					tcs.append(tc)
					c, tc = 0, {}
				else:
					c += 1
		
		for dt in date_range(self.date_from,self.date_to):
			tc = next(filter(lambda tc: tc['day'] == dt.day, tcs), None)
			currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
			rates = currency.rate_ids
			rate = rates.filtered(lambda rate: rate.name == dt)
			if tc:
				if rate:
					rate.write({'purchase_type': tc['purchase_type'],
								'sale_type': tc['sale_type'],
								'rate': tc['rate']})
				else:
					currency.write({'rate_ids':[(0, 0, {'name': dt,
														'purchase_type': tc['purchase_type'],
														'sale_type': tc['sale_type'],
														'rate': tc['rate']})
												]
									})
			else:
				last_rate = recursive_rate_call(dt)
				if rate:
					rate.write({'purchase_type': last_rate.purchase_type,
								'sale_type': last_rate.sale_type,
								'rate': last_rate.rate})
				else:
					currency.write({'rate_ids':[(0, 0, {'name': dt,
														'purchase_type': last_rate.purchase_type,
														'sale_type': last_rate.sale_type,
														'rate': last_rate.rate})
												]
									})