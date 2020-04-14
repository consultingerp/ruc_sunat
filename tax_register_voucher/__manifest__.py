# -*- encoding: utf-8 -*-
{
	'name': 'Tax Register Voucher',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account','base','account_base_it','account_fields_it'],
	'version': '1.0',
	'description':"""
	Detalle de Base e Impuestos en Lineas de Asiento Contable
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'views/account_account_tag.xml',
			'views/account_move.xml'
			],
	'installable': True
}
