# -*- coding: utf-8 -*-

from odoo import models, fields, api
from decimal import *
from odoo.exceptions import UserError
import json
from datetime import *
import urllib3
FACT_DATA_LABELS = ['Nro Documento Emisor : ','Tipo de Comprobante : ','Serie : ','Numero : ','IGV : ','Total : ','Fecha Emision : ',
					'Tipo de Documento : ','Nro de Documento : ','Codigo Hash : ', '']
class AccountMove(models.Model):
	_inherit = 'account.move'

	op_type_sunat_id = fields.Many2one('einvoice.catalog.51',string='Tipo de Operacion SUNAT')
	debit_note_type_id = fields.Many2one('einvoice.catalog.10',string='Tipo de Nota de Debito')
	credit_note_type_id = fields.Many2one('einvoice.catalog.09',string='Tipo de Nota de Credito')
	related_code = fields.Char(related='type_document_id.code',store=True)
	hash_code = fields.Char(string='Codigo Hash',copy=False)
	print_version = fields.Char(string='Version Impresa',copy=False)
	qr_code = fields.Char(string='Codigo QR',copy=False)
	print_web_version = fields.Char(string='Version Impresa Web',copy=False)
	file_name = fields.Char(copy=False)
	binary_version = fields.Binary(string='Version Binaria',copy=False)
	billing_type = fields.Selection([('0','Nubefact')],string='Tipo de Facturador')
	einvoice_id = fields.Many2one('einvoice',string='Facturacion Electronica',copy=False)
	is_advance = fields.Boolean(string='Es un Anticipo',default=False)
	advance_ids = fields.Many2many('account.move','invoice_advance_default_rel','move_id','advance_id',string='Anticipos',copy=False)
	sunat_state = fields.Selection([('0','Esperando Envio'),
									('1','Aceptada por SUNAT'),
									('2','Rechazada'),
									('3','Enviado')],string='Estado de Facturacion',default='0',copy=False)

	@api.model
	def create(self,vals):
		t = super(AccountMove,self).create(vals)
		if t.type in ['out_invoice','out_refund']:
			t.billing_type = self.env['main.parameter'].search([('company_id','=',self.env.company.id)],limit=1).billing_type or None
			catalog = self.env['einvoice.catalog.51'].search([('code','=','0101')])
			if not t.op_type_sunat_id and catalog:
				t.op_type_sunat_id = catalog.id
		return t

	#Function to be sure that the data is correct
	def verify_invoice_data(self,parameters):
		if self.hash_code:
			raise UserError('Este documento ya fue enviado')
		if not parameters.igv_tax_id:
			raise UserError('No se ha configurado un Impuesto IGV en Parametros Generales de Contabilidad en la Pestaña de Facturacion Electronica')
		if not parameters.advance_product_ids:
			raise UserError('No se ha configurado ningun Producto Anticipo en Parametros Generales de Contabilidad en la Pestaña de Facturacion Electronica')
		if not self.type_document_id.pse_code:
			raise UserError('El tipo de Documento no tiene Codigo de Facturador')
		if self.type_document_id.pse_code in ['3','4']:
			if len(self.doc_invoice_relac) != 1:
				raise UserError('El numero de lineas de Documentos Relacionados debe tener un item para Notas de Credito o Debito')
			if not self.doc_invoice_relac[0].type_document_id.pse_code:
				raise UserError('El Tipo de Documento del Comprobante Relacionado no tiene codigo definido')
			if len(self.doc_invoice_relac[0].nro_comprobante.split('-')) != 2:
				raise UserError('El Nro del Comprobante Relacionado no tiene el formato adecuado Ejem: "F001-000002"')
		if not self.ref:
			raise UserError('La referencia es un campo obligatorio')
		else:
			if len(self.ref.split('-')) != 2:
				raise UserError('La referencia no tiene el formato adecuado "Ejem: F001-000002"')
		if not self.op_type_sunat_id.pse_code:
			raise UserError('El Tipo de Operacion SUNAT no tiene Codigo de Facturador')
		if not self.partner_id.l10n_latam_identification_type_id.code_sunat:
			raise UserError('El partner no tiene su Tipo de Documento o su Tipo de Documento no tiene codigo sunat')
		if not self.partner_id.vat:
			raise UserError('El partner no tiene Numero de Documento')
		if not self.partner_id.name:
			raise UserError('El partner no tiene Nombre')
		if self.ref.split('-')[0][0] != 'B':
			if not self.partner_id.street:
				raise UserError('La direccion del partner es un campo obligatorio para este Tipo de Documento')
		if not self.invoice_date:
			raise UserError('La Fecha de Emision es un campo obligatorio')
		if not self.currency_id.pse_code:
			raise UserError('La moneda seleccionada no tiene su Codigo de Facturador')
		if not parameters.igv_tax_id.amount:
			raise UserError('No se ha configurado porcentaje en el impuesto seleccionado en Parametros Generales de Contabilidad')
		if self.currency_id.name != 'PEN' and not self.currency_rate:
			raise UserError('El Tipo de Cambio es obligatorio cuando se utiliza una moneda que no es Soles')
		if self.type == 'out_refund' and self.type_document_id.code == '07' and not self.credit_note_type_id.code:
			raise UserError('No se ha seleccionado Tipo de Nota de Credito o esta no tiene codigo')
		if self.type == 'out_invoice' and self.type_document_id.code == '08' and not self.debit_note_type_id.code:
			raise UserError('No se ha seleccionado Tipo de Nota de Debito o esta no tiene codigo')
		if not next(filter(lambda s:s.serie_id == self.serie_id,parameters.serial_nubefact_lines),None):
			raise UserError('No se ha configurado una linea de Facturacion para la Serie de este Comprobante')
		advance_counter = 0
		for line in self.invoice_line_ids:
			advance_product = next(filter(lambda a_line:a_line.product_id == line.product_id,parameters.advance_product_ids),None)
			if advance_product:
				advance_counter += 1
			if not advance_product and line.product_id.type in ['service','product'] and not line.product_id.onu_code.code:
				raise UserError('La linea con descripcion %s no tiene Codigo ONU asociado en su producto' % line.name)
			for tax in line.tax_ids:
				if tax.name != 'ICBPER' and not tax.eb_afect_igv_id.pse_code:
					raise UserError('La linea con descripcion %s tiene algun impuesto distinto a ICBPER sin tipo de afectacion o sin codigo de facturador en dicho tipo de afectacion' % line.name)
				if not tax.eb_tributes_type_id:
					raise UserError('La linea con descripcion %s tiene algun impuesto sin tipo de tributo' % line.name)
				if self.op_type_sunat_id.pse_code == '2':
					if tax.eb_afect_igv_id.pse_code != '16':
						raise UserError('Si el tipo de Operacion es Exportacion se debe utilizar el impuesto Exportacion en todas las lineas del Comprobante')
					
		if advance_counter > 0 and not self.is_advance:
			if advance_counter != len(self.advance_ids):
				raise UserError('El numero de Anticipos relacionados a este Comprobante es distinto a las lineas de anticipo existentes')
			for advance in self.advance_ids:
				if not advance.ref or len(advance.ref.split('-')) != 2:
					raise UserError('La linea de anticipo con descripcion %s no tiene referencia o dicha referencia no tiene el formato adecuado en su Comprobante "Ejem: F001-000002"' % line.name)
				if not advance.type_document_id:
					raise UserError('La linea de anticipo con descripcion %s no tiene Tipo de Documento asociado en su Comprobante' % line.name)
				if advance.type_document_id != self.type_document_id:
					raise UserError('La line de anticipo con descripcion %s no puede tener un Comprobante con un Tipo de Documento distinto al Comprobante Padre' % line.name)

	def generate_lines(self,line,advance_product,advance_regularization):
		tax_included = next(filter(lambda t:t.price_include,line.tax_ids),None)
		tax_line = next(filter(lambda tax:tax.eb_tributes_type_id and tax.eb_tributes_type_id.code != '7152',line.tax_ids),None)
		tax_percentage = tax_line.amount/100
		quantity = abs(line.quantity) if line.product_id == advance_product and not self.is_advance else line.quantity
		price_subtotal = abs(line.price_subtotal) if line.product_id == advance_product and not self.is_advance else line.price_subtotal
		if tax_included:
			price = line.price_unit - line.price_unit * tax_percentage
			price_igv = line.price_unit
		else:
			price = line.price_unit
			price_igv = line.price_unit + line.price_unit * tax_percentage
		discount = (price * quantity) * (line.discount/100)
		igv = price_subtotal * tax_percentage
		igv_type = next(filter(lambda tax:tax.eb_afect_igv_id,line.tax_ids)).eb_afect_igv_id.pse_code
		bag_tax = next(filter(lambda tax:tax.eb_tributes_type_id and tax.eb_tributes_type_id.code == '7152',line.tax_ids),None)
		bag_tax = quantity * bag_tax.amount if bag_tax else 0
		total = price_subtotal + igv + bag_tax
		onu_code = line.product_id.onu_code.code if advance_product != line.product_id and line.product_id.type in ['service','product'] else ""
		#Creating json line to send to Nubefact
		ebill_line = {
			"unidad_de_medida": 'ZZ' if line.product_id.type == 'service' else 'NIU',
			"codigo": line.product_id.default_code if line.product_id.default_code else '',
			"descripcion": line.name + ' (Gratuita)' if igv_type in ['2','3','4','5','6','7','10','11','12','13','14','15'] else line.name,
			"cantidad": quantity,
			"valor_unitario": price,
			"precio_unitario": price_igv,
			"descuento": discount,
			"subtotal": price_subtotal,
			"tipo_de_igv": igv_type,
			"igv": igv,
			"impuesto_bolsas": bag_tax,
			"total": total,
			"anticipo_regularizacion": "false",
			"anticipo_documento_serie": "",
			"anticipo_documento_numero": "",
			"codigo_producto_sunat": onu_code
		}
		#Creating altern line to save into another model just for informative reasons
		einvoice_line = {
			'move_line_id': line.id,
			'code': line.product_id.default_code,
			'uom': 'ZZ' if line.product_id.type == 'service' else 'NIU',
			'unit_value': price,
			'unit_price': price_igv,
			'discount_value': discount,
			'percentage_discount': line.discount,
			'sunat_product_code': onu_code,
			'igv_type': igv_type,
			'subtotal': price_subtotal,
			'igv': igv,
			'icbper': bag_tax,
			'total': total,
			'advance_regularization': False
		}
		if advance_regularization:
			ebill_line['anticipo_regularizacion'] = "true"
			einvoice_line['advance_regularization'] = True
			ebill_line['anticipo_documento_serie'] = einvoice_line['advance_document_serie'] = line.move_id.ref.split('-')[0]
			ebill_line['anticipo_documento_numero'] = einvoice_line['advance_document_number'] = line.move_id.ref.split('-')[1][1:]
		line.einvoice_line_id.unlink()
		line.write({'einvoice_line_id': self.env['einvoice.line'].create(einvoice_line).id})
		return ebill_line

	def send_ebill(self):
		parameters = self.env['main.parameter'].search([('company_id','=',self.env.company.id)],limit=1)
		self.verify_invoice_data(parameters)
		fact_line = next(filter(lambda s:s.serie_id == self.serie_id,parameters.serial_nubefact_lines))
		#Defining variables
		ebill_lines, invoice_with_advance, exportation = [], False, None
		total_saved, total_free, total_exonerate, total_inafect, total_discount, total_igv, total_advance, total_icbper = 0, 0, 0, 0, 0, 0, 0, 0

		for line in self.invoice_line_ids:
			exportation_type = next(filter(lambda tax:tax.eb_afect_igv_id and tax.eb_afect_igv_id.code == '40',line.tax_ids),None)
			if exportation_type:
				exportation = True if exportation_type.eb_tributes_type_id.code == '9995' else False
			advance_product = next(filter(lambda a_line:a_line.product_id == line.product_id,parameters.advance_product_ids),None)
			if not advance_product or self.is_advance:
				ebill_lines.append(self.generate_lines(line,advance_product,False))
		for advance in self.advance_ids:
			for adv_line in advance.invoice_line_ids:
				advance_product = next(filter(lambda a_line:a_line.product_id == adv_line.product_id,parameters.advance_product_ids),None)
				ebill_lines.append(self.generate_lines(adv_line,advance_product,True))
			
		#Defining flag to know if the invoice is free or not
		free_flag = True
		for e_line in ebill_lines:
			total_icbper += e_line['impuesto_bolsas']
			total_discount += e_line['descuento']
			total_igv += e_line['igv']
			if e_line['tipo_de_igv'] in ['1']:
				free_flag = False
				total_saved += e_line['subtotal']
			if e_line['tipo_de_igv'] in ['2','3','4','5','6','7','10','11','12','13','14','15']:
				total_free += e_line['subtotal']
			if e_line['tipo_de_igv'] in ['8']:
				total_exonerate += e_line['subtotal']
				free_flag = False
			if e_line['tipo_de_igv'] in ['9']:
				total_inafect += e_line['subtotal']
				free_flag = False
			if e_line['tipo_de_igv'] in ['16']:
				if exportation:
					total_inafect += e_line['subtotal']
					free_flag = False
				else:
					total_free += e_line['subtotal']
			if e_line['anticipo_regularizacion'] == "true":
				invoice_with_advance = True
				total_advance +=  e_line['subtotal']
				free_flag = False
		head_total = total_saved + total_inafect + total_exonerate + total_igv if not free_flag else 0
		#Creating json's header to send to Nubefact
		ebill_json = {
			"operacion": "generar_comprobante",
			"tipo_de_comprobante": self.type_document_id.pse_code,
			"serie": self.ref.split('-')[0],
			"numero": self.ref.split('-')[1],
			"sunat_transaction": self.op_type_sunat_id.pse_code if not invoice_with_advance else 4,
			"cliente_tipo_de_documento": self.partner_id.l10n_latam_identification_type_id.code_sunat,
			"cliente_numero_de_documento": self.partner_id.vat,
			"cliente_denominacion": self.partner_id.name,
			"cliente_direccion": self.partner_id.street,
			"cliente_email": self.partner_id.email,
			"cliente_email_1": "",
			"cliente_email_2": "",
			"fecha_de_emision": datetime.strftime(self.invoice_date,'%Y-%m-%d'),
			"fecha_de_vencimiento": datetime.strftime(self.invoice_date_due,'%Y-%m-%d'),
			"moneda": self.currency_id.pse_code,
			"tipo_de_cambio": self.currency_rate if self.currency_id.name != 'PEN' else "",
			"porcentaje_de_igv": float(Decimal(str(parameters.igv_tax_id.amount)).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)),
			"descuento_global": "",
			"total_descuento": total_discount,
			"total_anticipo": total_advance,
			"total_gravada": total_saved,
			"total_inafecta": total_inafect,
			"total_exonerada": total_exonerate,
			"total_igv": total_igv,
			"total_gratuita": total_free,
			"total_otros_cargos": "",
			"total_impuestos_bolsas": total_icbper,
			"total": head_total,
			"percepcion_tipo": "",
			"percepcion_base_imponible": "",
			"total_percepcion": "",
			"total_incluido_percepcion": "",
			"detraccion": "false",
			"observaciones": self.narration,
			"documento_que_se_modifica_tipo": self.doc_invoice_relac[0].type_document_id.pse_code if self.type_document_id.pse_code in ['3','4'] else "",
			"documento_que_se_modifica_serie": self.doc_invoice_relac[0].nro_comprobante.split('-')[0] if self.type_document_id.pse_code in ['3','4'] else "",
			"documento_que_se_modifica_numero": self.doc_invoice_relac[0].nro_comprobante.split('-')[1] if self.type_document_id.pse_code in ['3','4'] else "",
			"tipo_de_nota_de_credito": int(self.credit_note_type_id.code) if self.type == 'out_refund' and self.type_document_id.pse_code == '3' else "",
			"tipo_de_nota_de_debito": int(self.debit_note_type_id.code) if self.type == 'out_invoice' and self.type_document_id.pse_code == '4' else "",
			"enviar_automaticamente_a_la_sunat": "false",
			"enviar_automaticamente_al_cliente": "true" if self.partner_id.email else "false",
			"codigo_unico": "",
			"condiciones_de_pago": self.invoice_payment_term_id.name if self.invoice_payment_term_id else '',
			"medio_de_pago": "",
			"placa_vehiculo": "",
			"orden_compra_servicio": "",
			"tabla_personalizada_codigo": "",
			"formato_de_pdf": ""
		}
		ebill_json.update({"items":ebill_lines})
		#Creating alternative header just for informative reasons
		einvoice = {
			"move_id": self.id,
			"total_saved": total_saved,
			"total_inafect": total_inafect,
			"total_exonerate": total_exonerate,
			"total_free": total_free,
			"total_discount": total_discount,
			"total_advance": total_advance,
			"total_igv": total_igv,
			"total_icbper": total_icbper,
			"total_voucher": head_total
		}
		#Deleting Informative table in case exits one cause i don't want to have trash data
		self.einvoice_id.unlink()
		self.write({'einvoice_id': self.env['einvoice'].create(einvoice).id})
		http = urllib3.PoolManager()
		try:
			r = http.request('POST',
							fact_line.nubefact_path,
							headers = {'Content-Type':'application/json',
									   'Authorization':'Token token = "%s"'%fact_line.nubefact_token},
							body = json.dumps(ebill_json))
		except urllib3.exceptions.HTTPError as e:
			raise UserError("Error al intentar conectarse: \n\t %s"%e.reason)
		response = json.loads(r.data.decode('utf-8'))
		if 'errors' in response:
			raise UserError('Respuesta del Facturador: ' + response['errors'])
		if 'codigo_hash' in response:
			self.hash_code = response['codigo_hash']
		if 'enlace_del_pdf' in response:
			self.print_version = response['enlace_del_pdf']
		if 'cadena_para_codigo_qr' in response:
			self.qr_code = response['cadena_para_codigo_qr']
		if 'aceptada_por_sunat' in response:
			self.sunat_state = '3'
		return self.env['popup.it'].get_message("SE ENVIO EL COMPROBANTE SATISFACTORIAMENTE")

	def query_ebill(self):
		parameters = self.env['main.parameter'].search([('company_id','=',self.env.company.id)],limit=1)
		fact_line = next(filter(lambda s:s.serie_id == self.serie_id,parameters.serial_nubefact_lines))
		if not self.type_document_id.pse_code:
			raise UserError('El Tipo de Documento no tiene Codigo de Facturador')
		if not self.ref:
			raise UserError('No existe una referencia definida')
			if len(self.ref.split('-')) != 2:
				raise UserError('La referencia no tiene el formato adecuado "Ejem: F001-000002"')
		ebill_json = {
			"operacion": "consultar_comprobante",
			"tipo_de_comprobante": self.type_document_id.pse_code,
			"serie": self.ref.split('-')[0],
			"numero": self.ref.split('-')[1],
		}
		http = urllib3.PoolManager()
		try:
			r = http.request('POST',
							fact_line.nubefact_path,
							headers = {'Content-Type':'application/json',
									   'Authorization':'Token token = "%s"'%fact_line.nubefact_token},
							body = json.dumps(ebill_json))
		except urllib3.exceptions.HTTPError as e:
			raise UserError("Error al intentar conectarse: \n\t %s"%e.reason)
		response = json.loads(r.data.decode('utf-8'))
		if 'errors' in response:
			raise UserError(response['errors'])
		if 'codigo_hash' in response:
			self.hash_code = response['codigo_hash']
		if 'enlace_del_pdf' in response:
			self.print_version = response['enlace_del_pdf']
		if 'cadena_para_codigo_qr' in response:
			self.qr_code = response['cadena_para_codigo_qr']
		if 'aceptada_por_sunat' in response:
			self.sunat_state = '1' if response['aceptada_por_sunat'] else '2'
		if 'sunat_description' in response and 'cadena_para_codigo_qr' in response:
			return self.env['popup.it'].get_message('RESPUESTA DEL FACTURADOR: \n %s \n Con la siguiente data: \n %s'%(
												response['sunat_description'],
												'\n'.join(FACT_DATA_LABELS[c] + str(i) for c,i in enumerate(response['cadena_para_codigo_qr'].split('|')))
											)
										)

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	einvoice_line_id = fields.Many2one('einvoice.line')

	def get_einvoice_line(self):
		if self.einvoice_line_id:
			return {
				'res_id':self.einvoice_line_id.id,
				'view_mode':'form',
				'res_model':'einvoice.line',
				'views':[[self.env.ref('ebill.view_einvoice_line_form').id,'form']],
				'type':'ir.actions.act_window',
				'target':'new'
			}