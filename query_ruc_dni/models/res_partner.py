# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import subprocess
import sys

def install(package):
	subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
	from suds.client import Client
except:
	install('suds-py3')

class ResPartner(models.Model):
	_inherit = 'res.partner'
	
	####### CONSULTA DNI #########
	related_identification = fields.Char(related='l10n_latam_identification_type_id.code_sunat',store=True)

	@api.model
	def default_get(self,fields):
		res = super(ResPartner,self).default_get(fields)
		res['name'] = 'Nombre'
		res['name_p']  = 'Nombre'
		res['last_name'] = 'Apellido Paterno'
		res['m_last_name'] = 'Apellido Materno'
		return res

	@api.onchange('company_type')
	def _set_street_default(self):
		if self.company_type == 'company':
			if self.l10n_latam_identification_type_id:
				if self.l10n_latam_identification_type_id.code_sunat == '06':
					self.street = 'Calle'
		else:
			self.street = ''

	@api.onchange('l10n_latam_identification_type_id')
	def _verify_document(self):
		if self.l10n_latam_identification_type_id:
			if self.l10n_latam_identification_type_id.code_sunat == '06' and self.company_type == 'company':
				self.street = 'Calle'
			else:
				self.street = ''
		else:
			self.street = ''

	def verify_dni(self):
		parameters = self.env['sale.main.parameter'].verify_query_parameters()
		if not self.vat:
			raise UserError("Debe seleccionar un DNI")
		client = Client(parameters.query_dni_url, faults = False, cachingpolicy = 1, location = parameters.query_dni_url)
		try: 
			result = client.service.consultar(str(self.vat),parameters.query_email,parameters.query_token,parameters.query_type)
		except Exception as e:
			raise UserError('No se encontro el DNI')
		texto = result[1].split('|')
		flag = False
		nombres = ''
		a_paterno = ''
		a_materno = ''
		for c in texto:
			tmp = c.split('=')
			if tmp[0] == 'status_id' and tmp[1] == '102':
				raise UserError('El DNI debe tener al menos 8 digitos de longitud')
			if tmp[0] == 'status_id' and tmp[1] == '103':
				raise UserError('El DNI debe ser un valor numerico')
			if tmp[0] == 'reniec_nombres' and tmp[1] != '':
				nombres = tmp[1]
				self.name_p = tmp[1]
			if tmp[0] == 'reniec_paterno' and tmp[1] != '':
				a_paterno = tmp[1]
				self.last_name = tmp[1]
			if tmp[0] == 'reniec_materno' and tmp[1] != '':
				a_materno = tmp[1]
				self.m_last_name = tmp[1]
		self.name = (nombres + " " + a_paterno + " " + a_materno).strip()
	####### CONSULTA DNI #########

	####### CONSULTA RUC #########
	ruc_state = fields.Char(string='RUC Estado')
	ruc_condition = fields.Char(string=u'RUC Condición')

	def verify_ruc(selfs):
		for self in selfs:
			if self.l10n_latam_identification_type_id == self.env['main.parameter'].search([],limit=1).dt_sunat_ruc:
				parameters = self.env['sale.main.parameter'].verify_query_parameters()
				client = Client(parameters.query_ruc_url, faults = False, cachingpolicy = 1, location = parameters.query_ruc_url)
				result = client.service.consultaRUC(self.vat,parameters.query_email,parameters.query_token,parameters.query_type)
				texto = result[1].split('|')
				flag = False
				for i in texto:
					tmp = i.split('=')
					if tmp[0] == 'status_id' and tmp[1] == '1':
						flag = True

				if flag:
					for j in texto:
						tmp = j.split('=')
						if tmp[0] == 'n1_alias':
							self.name = tmp[1]
						if tmp[0] == 'n1_direccion':
							self.street = tmp[1]
						if tmp[0] == 'n1_ubigeo':
							ubigeo = self.env['res.country.state'].search([('code','=',tmp[1])])
							if ubigeo:
								self.zip = tmp[1]
								pais = self.env['res.country'].search([('code','=','PE')]) 
								ubidepa = tmp[1][0:2]
								ubiprov = tmp[1][0:4]
								ubidist = tmp[1][0:6]

								departamento = self.env['res.country.state'].search([('code','=',ubidepa),('country_id','=',pais.id)])
								provincia  = self.env['res.country.state'].search([('code','=',ubiprov),('country_id','=',pais.id)])
								distrito = self.env['res.country.state'].search([('code','=',ubidist),('country_id','=',pais.id)])

								self.country_id = pais.id
								self.state_id = departamento.id
								self.province_id = provincia.id
								self.district_id = distrito.id
						if tmp[0] == 'n1_estado':
							self.ruc_state = tmp[1]
						if tmp[0] == 'n1_condicion':
							self.ruc_condition = tmp[1]
						
				else:
					raise UserError("El RUC es invalido.")	
	####### CONSULTA RUC #########