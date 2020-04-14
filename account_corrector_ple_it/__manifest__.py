# -- encoding: utf-8 --
{
	'name': 'CORRECTOR PLE IT',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account','account_base_it','account_fields_it','account_report_menu_it'],
	'version': '1.0',
	'description':"""
	Corrector de PLE de Compras y PLE de Ventas
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'views/account_ple_purchase_fix.xml',
		'views/account_ple_sale_fix.xml'
		],
	'installable': True
}