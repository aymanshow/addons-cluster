#!/usr/bin/python
# -*- encoding: utf-8 -*-
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://openerp.com.ve>).
#    All Rights Reserved
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#    Author: Cluster Brands
#    Copyright 2013 Cluster Brands
#    Designed By: Jose J Perez M <jose.perez@clusterbrands.com>
#    Coded by: Eduardo Ochoa  <eduardo.ochoa@clusterbrands.com.ve>
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
{
    'name': 'Cluster Brands Purchase Reports',
    'category': 'Purchase',
    'version': '1.0',
    'author': 'Cluster Brands',
    'website': 'http://www.clusterbrands.com',
    'description': """
    
This module contain a custom purchase
reports used by Cluster Brands C.A

Main features
-------------

    * request_qoutation report with a user signature and venezuelan 
      vat format
    * order report with a user signature and venezuelan vat format

""",
    'depends': [
        'l10n_ve_fiscal_book',
        'purchase',
        'report_qweb_cluster',
    ],
    'data': [        
        #'purchase_report.xml',
        'views/layouts.xml',
        'views/report_purchasequotation.xml',
        'views/report_purchaseorder.xml',
    ],
    'js': [
    ],
    'css':[
    ],
    'qweb': [
    ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
