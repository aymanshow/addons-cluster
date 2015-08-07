from openerp.osv import fields, osv
from openerp import tools
from openerp.tools.translate import _

class account_bank_statement(osv.Model):
    _inherit = 'account.bank.statement'
    _columns = {
            'instrument_id':fields.many2one('payment_instrument.instrument',
                'Payment Instrument', help="""Payment Instrument linked to Statement"""),
    }
    _order = 'journal_id, instrument_id'
