# -*- encoding: utf-8 -*-
{
	'name': 'Currency Rate Update',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account','base'],
	'version': '1.0',
	'description':"""
	Modificacion del modelo res.currency.rate
	Modificacion del modelo res.currency
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'views/currency_rate.xml',
			'views/res_currency.xml',
			'wizards/res_currency_wizard.xml'
			],
	'installable': True
}
