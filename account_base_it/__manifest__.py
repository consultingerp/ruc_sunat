# -*- encoding: utf-8 -*-
{
	'name': 'Account Base IT',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account','base','product','l10n_latam_base','account_accountant','popup_it'],
	'version': '1.0',
	'description':"""
	Creacion de Catalogos y Tablas
		-Catalogo 1 Codigo Tipo de Comprobante
		-Catalogo 6 Tipos de Documento de Identidad
		-Medio de Pago SUNAT
		-Codigo de Impuestos
		-Tipos Estados Financieros
		-Rubros Flujo de Efectivo
		-Rubros Cambios en el Patrimonio Neto
		-Año Fiscal
		-Periodos
		-Tipos de Cambio de Cierre
		-Flujo de Caja
		-Tabla de Parametros Modulo Contable
		-Tipos Contables
		-Tipos de Existencias
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/security.xml',
			'security/ir.model.access.csv',
			'data/einvoice_catalog_01.xml',
			'data/einvoice_catalog_payment.xml',
			'data/account_type_it.xml',
			'data/account_efective_type.xml',
			'data/account_patrimony_type.xml',
			'data/existence_type.xml',
			'views/account_bank_statement.xml',
			'views/account_cash_flow.xml',
			'views/account_efective_type.xml',
			'views/account_patrimony_type.xml',
			'views/account_period.xml',
			'views/account_type_close.xml',
			'views/account_type_it.xml',
			'views/einvoice_catalog_01.xml',
			'views/einvoice_catalog_06.xml',
			'views/einvoice_catalog_payment.xml',
			'views/it_invoice_serie.xml',
			'views/existence_type.xml',
			'views/main_parameter.xml',
			'views/menu_items.xml'
			],
	'installable': True
}
