# -*- encoding: utf-8 -*-
{
	'name': 'Query RUC and DNI',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['base','l10n_latam_base','sale_parameter','sale_management','account_fields_it'],
	'version': '1.0',
	'description':"""
	Modulo para consultar RUC y DNI mediante el uso de una API
	Para instalar este modulo es necesario instalar la libreria suds-py3 con el comando 'python -m pip install suds-py3' 
	""",
	'auto_install': False,
	'demo': [],
	'data': ['views/res_partner.xml'],
	'installable': True,
}
