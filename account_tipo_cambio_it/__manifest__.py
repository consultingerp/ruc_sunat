# -*- encoding: utf-8 -*-
{
	'name': 'TC Personalizado IT',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account','analytic','base','account_fields_it','account_batch_payment','product','stock_account'],
	'version': '1.0',
	'description':"""
	TC Personalizado en asientos contables
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'views/account_move.xml',
			],
	'installable': True
}
