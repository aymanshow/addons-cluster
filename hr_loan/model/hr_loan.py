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
import time
from openerp.osv import osv, fields
from openerp.tools.translate import _

class hr_loan(osv.Model):
    _name = "hr.loan"

    _rec_name = 'employee_name'

    def _get_loan_quota(self, cr, uid, ids, field_name, args, context=None):
        context = context or {}
        res = dict.fromkeys(ids)
        for loan in self.browse(cr, uid, ids, context=context):
            if loan.periods:
                res[loan.id] = (loan.amount / loan.periods) 
            else:
                res[loan.id] = 0.0
        return res
        
    def _compute_balance(self, cr, uid, ids, field_name, args, context=None):
        context = context or {}
        res = dict.fromkeys(ids, 0.0)
        for loan in self.browse(cr, uid, ids, context=context):
            amount = 0
            for balance in loan.balance_ids:
                amount+= balance.debit - balance.credit
            res[loan.id] = loan.amount - amount
        return res

    _columns = {
        'employee_id':fields.many2one('hr.employee', 'Employee', required=True, states={'approved': [('readonly', True)]}),
        'employee_name': fields.related('employee_id', 'name', type='text', string='Employee ', readonly=True), 
        'contract_id':fields.many2one('hr.contract', 'Contract', required=False, states={'approved': [('readonly', True)]}),
        'payroll_period_id': fields.many2one('hr.payroll.period', 'Start Payperiod', states={'approved': [('readonly', True)]}),
        'payperiod_date_start': fields.related('payroll_period_id', 'date_start', type='date', string='Start Date', readonly=True), 
        'payperiod_date_end': fields.related('payroll_period_id', 'date_end', type='date', string='End Date', readonly=True), 
        'type_id':fields.many2one('hr.loan.type', 'Type', required=True, states={'approved': [('readonly', True)]}), 
        'reason':fields.selection([
            ('apartment','Apartment'),
            ('health','Health'),
            ('studies','Studies')
            ], 'Reason', select=True, states={'approved': [('readonly', True)]}),
        'amount': fields.float('Amount', digits=(16, 2), required=False, states={'approved': [('readonly', True)]}), 
        'periods': fields.integer('Periods Numbers', states={'approved': [('readonly', True)]}), 
        'quota': fields.function(_get_loan_quota, method=True, type='float', string='Quota', states={'approved': [('readonly', True)]}),
        'details': fields.text('Details', states={'approved': [('readonly', True)]}),
        'move_id':fields.many2one('account.move', 'Move', required=False, ondelete='cascade'),
        'balance_ids' : fields.one2many('hr.loan.balance','loan_id', 'Loan Balance'),
        'balance': fields.function(_compute_balance, type='float', string='Balance', store=True),
        'state':fields.selection([
            ('to_submit','To Submit'),
            ('to_approve','To Approve'),
            ('approved','Approved'),
            ('declined', 'Declined')
            ], 'Status', readonly=True),
    }

    def unlink(self, cr, uid, ids, context=None):
        context = context or {}
        for loan in self.browse(cr, uid, ids, context=context):
            if loan.move_id:
                raise osv.except_osv( _('Error!'), _("The loan can not be deleted without first canceling the associated account movement"))
        return super(hr_loan, self).unlink(cr, uid, ids, context)

    def update_quota(self, cr, uid, ids, context=None):
        context = context or {}
        return True

    def onchange_contract(self, cr, uid, ids, contract_id, context=None):
       	context = context or {}
       	domain = [('schedule_id','=',False),('state','in',('open','actived'))]
        obj = self.pool.get('hr.contract')
        if contract_id:
            contract = obj.browse(cr, uid, contract_id, context=context)
            domain[0] = ('schedule_id','=', contract.schedule_id.id)
            return {'domain':{'payroll_period_id': domain}}
        else:
            res = {'payroll_period_id': False}
            return {'domain':{'payroll_period_id': domain}, 'value': res}

    def onchange_payroll_period(self, cr, uid, ids, payroll_period_id, context=None):
        context = context or {}
        obj = self.pool.get('hr.payroll.period')
        if payroll_period_id:
            period = obj.browse(cr, uid, payroll_period_id, context=context)
            res = {
                'payperiod_date_start': period.date_start,
                'payperiod_date_end': period.date_end
            }
        else:
            res = {
                'payperiod_date_start': False,
                'payperiod_date_end': False,
            }
        return {'value': res}

    def do_signal_to_draft(self, cr, uid, ids, context=None):
        context = context or {}
        return self.write(cr, uid, ids, {'state':'to_submit'}, context=context)

    def do_signal_to_approve(self, cr, uid, ids, context=None):
        context = context or {}
        return self.write(cr, uid, ids, {'state':'to_approve'}, context=context)
        
    def do_signal_approved(self, cr, uid, ids, context=None):
        context = context or {}
        line_ids = []
        move_pool = self.pool.get('account.move')
        period_pool = self.pool.get('account.period')
        pp_pool = self.pool.get('hr.payroll.period')
        precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Payroll')
        timenow = time.strftime('%Y-%m-%d')
        ctx = dict(context or {}, account_period_prefer_normal=True)
        search_periods = period_pool.find(cr, uid, timenow, context=ctx)
        period_id = search_periods[0]
        loan = self.browse(cr, uid, ids, context=context)[0]
        name = _('Loan for %s') % (loan.employee_id.name)
        move = {
            'date': timenow,
            'ref': name,
            'journal_id': loan.type_id.journal_id.id,
            'period_id': period_id,
        }
        debit_line = (0, 0, {
            'name': 'loan',
            'date': timenow,
            'partner_id': loan.employee_id.address_home_id.id,
            'account_id': loan.type_id.debit_account.id,
            'journal_id': loan.type_id.journal_id.id,
            'period_id': period_id,
            'debit': loan.amount,
            'credit': 0.0,
        })
        line_ids.append(debit_line)
        credit_line = (0, 0, {
            'name': 'loan',
            'date': timenow,
            'partner_id': loan.employee_id.address_home_id.id,
            'account_id': loan.type_id.credit_account.id,
            'journal_id': loan.type_id.journal_id.id,
            'period_id': period_id,
            'debit': 0.0,
            'credit': loan.amount,
        })
        line_ids.append(credit_line)
        move.update({'line_id': line_ids})
        move_id = move_pool.create(cr, uid, move, context=context)
        self.write(cr, uid, ids, {'move_id': move_id})
        return self.write(cr, uid, ids, {'state':'approved'}, context=context)
        

    def do_signal_decline(self, cr, uid, ids, context=None):
        context = context or {}
        return self.write(cr, uid, ids, {'state':'declined'}, context=context)
        
    def check_contract_and_period(self, cr, uid, ids, context=None):
        for brw in self.browse(cr, uid, ids, context=context):
            if not brw.contract_id:
                raise osv.except_osv( _('Error!'), _("You should select a valid contract to approve this loan"))
            if not brw.payroll_period_id:
                raise osv.except_osv( _('Error!'), _("You should select a valid start 'Payperiod' to approve this loan"))
        return True
        
class hr_loan_balance(osv.Model):
    _name = "hr.loan.balance"
    
    _columns = {
        'loan_id': fields.many2one('hr.loan', 'Loan', required=True),
        'reference': fields.char('Reference', size=255),
        'date': fields.date('Date', required=True),
        'move_id': fields.many2one('account.move.line', 'Accounting Entry', required=True),
        'debit': fields.related('move_id', 'debit', type='float', string='Debit'),
        'credit': fields.related('move_id', 'credit', type='float', string='Debit'),
        'account_id': fields.related('move_id', 'account_id', type='many2one',relation="account.account", string='Account'),
    }

class hr_loan_type(osv.Model):
    _name = "hr.loan.type"

    _columns = {
        'name': fields.char('Name', size=255, required=True),
        'code': fields.char('Code', size=55, required=True), 
        'max_amount': fields.float('Max. Amount ', digits=(16, 2), required=False), 
        'min_discount': fields.float('Min. Discount ', digits=(16, 2), required=False), 
        'journal_id': fields.many2one('account.journal', 'Journal', required=True), 
        'debit_account':fields.many2one('account.account', 'Debit Account', required=True), 
        'credit_account':fields.many2one('account.account', 'Credit Account', required=True), 
        'rule_id': fields.many2one('hr.salary.rule', 'Salary Rule', required=True),
        'details': fields.text('Details'), 
    }
