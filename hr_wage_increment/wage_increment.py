#-*- coding:utf-8 -*-
#
#
#    Copyright (C) 2011 Michael Telahun Makonnen <mmakonnen@gmail.com>.
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#

from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp import netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _


class wage_increment(osv.osv):

    _name = 'hr.contract.wage.increment'
    _description = 'HR Contract Wage Adjustment'

    def _calculate_difference(self, cr, uid, ids, field_name, args, context=None):

        res = dict.fromkeys(ids)
        for incr in self.browse(cr, uid, ids, context=context):
            if incr.wage >= incr.contract_id.wage:
                percent = ((incr.wage / incr.contract_id.wage) - 1.0) * 100.0
            else:
                percent = (1.0 - (incr.wage / incr.contract_id.wage)) * -100.0
            res[incr.id] = {
                'wage_difference': incr.wage - incr.current_wage,
                'wage_difference_percent': percent,
            }

        return res

    def _get_department(self, cr, uid, ids, field_name, arg, context=None):

        res = dict.fromkeys(ids, False)
        for incr in self.browse(cr, uid, ids, context=context):
            res[incr.id] = incr.employee_id.department_id.id,

        return res

    _columns = {
        'effective_date': fields.date('Effective Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'wage': fields.float('New Wage', digits_compute=dp.get_precision('Payroll'), required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'new_contract_id': fields.many2one('hr.contract', 'New Contract', readonly=True),
        'contract_id': fields.many2one('hr.contract', 'Contract', required=True),
        'current_wage': fields.float('Current Wage',digits_compute=dp.get_precision('Payroll'), readonly=True),
        'wage_difference': fields.function(_calculate_difference, type='float', method=True,
                                           string='Difference', multi='diff', readonly=True),
        'wage_difference_percent': fields.function(_calculate_difference, type='float', method=True,
                                                   string='Percentage', multi='diff', readonly=True),
        'employee_id': fields.many2one('hr.employee', 'Employee',required=True),
        'job_id': fields.related('contract_id', 'job_id', relation='hr.job',
                                 type='many2one', string='Job', store=True, readonly=True),
        'department_id': fields.related('employee_id', 'department_id', relation='hr.department',
                                        type='many2one', string='Department', store=True, readonly=True),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('confirm', 'Confirmed'),
            ('applied', 'Applied'),
            ('decline', 'Declined')
        ], 'State', readonly=True),
        'run_id': fields.many2one('hr.contract.wage.increment.run', 'Batch Run',
                                  readonly=True, ondelete='cascade'),
    }

    def _get_contract_data(self, cr, uid, field_list, context=None):

        if context == None:
            context = {}
        employee_id = self._get_employee(cr, uid, context=context)
        ee_data = self.pool.get('hr.employee').read(
            cr, uid, employee_id, ['contract_id'], context=context)
        contract_id = ee_data.get('contract_id', False)[0]
        if not contract_id:
            return False

        data = self.pool.get('hr.contract').read(
            cr, uid, contract_id, field_list, context=context)

        return data

    def _get_contract_id(self, cr, uid, context=None):

        data = self._get_contract_data(cr, uid, ['id'], context)
        return data.get('id', False)

    def _get_employee(self, cr, uid, context=None):

        if context == None:
            context = {}
        employee_id = context.get('active_id', False)

        return employee_id

    def _get_effective_date(self, cr, uid, context=None):

        contract_id = self._get_contract_id(cr, uid, context=context)
        if not contract_id:
            return False

        contract = self.pool.get('hr.contract').browse(
            cr, uid, contract_id, context=context)
        if contract.pps_id:
            first_day = 1
            if contract.pps_id.type == 'monthly':
                first_day = contract.pps_id.mo_firstday
            dThisMonth = datetime.strptime(datetime.now().strftime(
                '%Y-%m-' + first_day), DEFAULT_SERVER_DATE_FORMAT).date()
            dNextMonth = datetime.strptime((datetime.now() + relativedelta(months=+1)).strftime(
                '%Y-%m-' + first_day), DEFAULT_SERVER_DATE_FORMAT).date()
            if dThisMonth < datetime.now().date():
                return dNextMonth.strftime(DEFAULT_SERVER_DATE_FORMAT)
            else:
                return dThisMonth.strftime(DEFAULT_SERVER_DATE_FORMAT)

        return False

    def onchange_employee(self, cr, uid, ids, employee_id, context=None):
        context = context or {}
        res = {'contract_id': False, 'current_wage': 0.0}
        return {'value':res}

    def onchange_contract(self, cr, uid, ids, contract_id, context=None):
        context = context or {}
        obj = self.pool.get('hr.contract')
        res = {'current_wage':0.0}
        if contract_id:
            contract = obj.browse(cr, uid, contract_id, context=context)
            res.update({'current_wage': contract.wage})
        return {'value':res}

    _defaults = {
        'state': 'draft',
    }

    _rec_name = 'effective_date'

    def _check_state(self, cr, uid, wage_incr, context=None):

        wage_incr_ids = self.search(cr, uid, [
            ('contract_id', '=', wage_incr.contract_id.id),
            ('state', 'in', [
                'draft', 'confirm']),
            ('id', '!=', wage_incr.id),
        ],
            context=context)
        if len(wage_incr_ids) > 0:
            data = self.pool.get('hr.contract').read(
                cr, uid, wage_incr.contract_id.id, ['name'], context=context)
            raise osv.except_osv(
                _('Warning'), _('There is already another wage adustment in progress for this contract: %s.') % (data['name']))

        contract_obj = self.pool.get('hr.contract')
        data = contract_obj.read(
            cr, uid, wage_incr.contract_id.id, ['state', 'date_end'], context=context)

        if data.get('date_end', False) and data['date_end'] != '':
            dContractEnd = datetime.strptime(
                data['date_end'], DEFAULT_SERVER_DATE_FORMAT)
            dEffective = datetime.strptime(
                wage_incr.effective_date, DEFAULT_SERVER_DATE_FORMAT)
            if dEffective >= dContractEnd:
                data = self.pool.get('hr.contract').read(
                    cr, uid, wage_incr.contract_id.id, ['name'], context=context)
                raise osv.except_osv(
                    _('Warning!'), _('The contract end date is on or before the effective date of the adjustment: %s') % (data['name']))

        return True

    def try_contract_wage_applied(self, cr, uid, context=None):
        context = context or {}
        d = datetime.now().date()
        current_date = d.strftime(DEFAULT_SERVER_DATE_FORMAT)
        domain = [('effective_date', '<=', current_date),('state', '=', 'confirm')]
        ids = self.search(cr, uid, domain, context=context)
        self.action_wage_increment(cr, uid, ids, context=context)
        return True

    def try_wage_increment_run_applied(self, cr, uid, run_id, context=None):      
        context = context or {}
        run_obj = self.pool.get('hr.contract.wage.increment.run')
        wi_obj = self.pool.get('hr.contract.wage.increment')
        run = run_obj.browse(cr, uid, run_id, context=context)
        dom = [('run_id', '=', run_id),('state', '=', 'applied')]
        wi_ids = wi_obj.search(cr, uid, dom, context=context)
        if len(wi_ids) == len(run.increment_ids):
            wkf = netsvc.LocalService('workflow')
            wkf.trg_validate(uid, 'hr.contract.wage.increment.run', run_id, 'signal_applied', cr)
            return True
        return False

    def action_wage_increment(self, cr, uid, ids, context=None):
        context = context or {}
        hr_obj = self.pool.get('hr.contract')

        for wi in self.browse(cr, uid, ids, context=context):

            if wi.wage_difference > -0.01 and wi.wage_difference < 0.01:
                continue

            self._check_state(cr, uid, wi, context=context)

            data = hr_obj.read(cr, uid, wi.contract_id.id,['notes'], context=context)
            notes = data.get('notes', False)
            if not notes:
                notes = ''
            notes = notes + '\n' + str(datetime.now().date()) + ' wage increment adjustment from ' + str(wi.contract_id.wage) + ' to ' + str(wi.wage)
            data['notes'] = notes
            data['wage'] = wi.wage
            c_id = hr_obj.write(cr, uid, wi.contract_id.id, data, context=context)
            wkf = netsvc.LocalService('workflow')
            wkf.trg_validate(uid, 'hr.contract.wage.increment', wi.id, 'signal_applied', cr)
            if wi.run_id:
                self.try_wage_increment_run_applied(cr, uid, wi.run_id.id, context=context)
        return

    def create(self, cr, uid, vals, context=None):
        context = context or {}
        c_obj = self.pool.get('hr.contract')
        data = c_obj.read(cr, uid, vals['contract_id'],
                           ['name', 'date_start','wage'],
                           context=context)
        vals.update({'current_wage':data['wage']})

        # Check that the contract start date is before the effective date
        if vals['effective_date'] <= data['date_start']:
            raise osv.except_osv(
                _('Error'), _('The effective date of the adjustment must be after the contract start date. Contract: %s.') % (data['name']))

        wage_incr_ids = self.search(cr, uid, [
            ('contract_id', '=', vals['contract_id']),
            ('state', 'in', [
                'draft', 'confirm']),
        ],
            context=context)
        if len(wage_incr_ids) > 0:
            raise osv.except_osv(
                _('Warning'), _('There is already another wage adustment in progress for this contract: %s.') % (data['name']))

        return super(wage_increment, self).create(cr, uid, vals, context=context)

    def do_signal_confirm(self, cr, uid, ids, context=None):

        for wi in self.browse(cr, uid, ids, context=context):
            self._check_state(cr, uid, wi, context=context)
            self.write(cr, uid, wi.id, {'state': 'confirm'}, context=context)

    def do_signal_applied(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'applied'}, context=context)

    def unlink(self, cr, uid, ids, context=None):

        for incr in self.browse(cr, uid, ids, context=context):
            if incr.state in ['applied']:
                raise osv.except_osv(_('The record cannot be deleted!'), _(
                    'You may not delete a record that is in a %s state:\nEmployee: %s') % (incr.state, incr.employee_id.name))

        return super(wage_increment, self).unlink(cr, uid, ids, context=context)


class wage_increment_run(osv.osv):

    _name = 'hr.contract.wage.increment.run'
    _description = 'Wage Increment Batches'

    _inherit = ['ir.needaction_mixin']

    _columns = {
        'name': fields.char('Name', size=64, required=True, readonly=True,
                            states={'draft': [('readonly', False)]}),
        'effective_date': fields.date('Effective Date', required=True, readonly=True,
                                      states={'draft': [('readonly', False)]}),
        'type': fields.selection([
            ('fixed', 'Fixed Amount'),
            ('percent', 'Percentage'),
            ('final', 'Final Amount'),
            ('manual', 'Manual'),
        ], 'Type', required=True, readonly=True,
            states={'draft': [('readonly', False)]}),
        'adjustment_amount': fields.float('Adjustment Amount',
                                          digits_compute=dp.get_precision('Payroll'), required=True,
                                          readonly=True, states={
                                              'draft': [('readonly', False)]}),
        'increment_ids': fields.one2many('hr.contract.wage.increment', 'run_id', 'Adjustments',
                                         required=False, readonly=False,
                                         states={
                                             'confirm': [('readonly', False)],
                                             'applied': [('readonly', True)],
                                             'decline': [('readonly', True)]}),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('confirm', 'Confirmed'),
            ('applied', 'Applied'),
            ('decline', 'Declined')
        ], 'State', readonly=True),
    }

    _defaults = {
        'state': 'draft',
    }

    def _needaction_domain_get(self, cr, uid, context=None):

        users_obj = self.pool.get('res.users')
        domain = []

        if users_obj.has_group(cr, uid, 'base.group_hr_manager'):
            domain = [('state', 'in', ['confirm'])]
            return domain

        return False

    def unlink(self, cr, uid, ids, context=None):

        if isinstance(ids, (int, long)):
            ids = [ids]

        for run in self.browse(cr, uid, ids, context=context):
            if run.state in ['applied']:
                raise osv.except_osv(_('The adjustment run cannot be deleted!'), _(
                    'You may not delete a wage adjustment that is in the %s state.') % (run.state))

        return super(wage_increment_run, self).unlink(cr, uid, ids, context=context)

    def _state(self, cr, uid, ids, signal, state, context=None):

        wkf = netsvc.LocalService('workflow')
        for run in self.browse(cr, uid, ids, context=context):
            [wkf.trg_validate(uid, 'hr.contract.wage.increment', incr.id, signal, cr)
             for incr in run.increment_ids]
            self.write(cr, uid, run.id, {'state': state}, context=context)
        return True

    def state_confirm(self, cr, uid, ids, context=None):

        return self._state(cr, uid, ids, 'signal_confirm', 'confirm', context)

    def state_applied(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'applied'}, context=context)

    def state_decline(self, cr, uid, ids, context=None):

        return self._state(cr, uid, ids, 'signal_decline', 'decline', context)


class hr_contract(osv.Model):

    _name = 'hr.contract'
    _inherit = 'hr.contract'

    def state_pending_done(self, cr, uid, ids, context=None):

        for i in ids:
            wi_ids = self.pool.get('hr.contract.wage.increment').search(cr, uid, [
                ('contract_id', '=', i),
                ('state', 'in', [
                    'draft', 'confirm']),
            ],
                context=context)
        if len(wi_ids) > 0:
            data = self.pool.get('hr.contract').read(cr, uid, i, ['name'],
                                                     context=context)
            raise osv.except_osv(_('Error'),
                                 _('There is a wage adustment in progress for this contract. Either delete the adjustment or delay the termination of contract %s.') % (data['name']))
        return super(hr_contract, self).state_pending_done(cr, uid, ids, context=context)
