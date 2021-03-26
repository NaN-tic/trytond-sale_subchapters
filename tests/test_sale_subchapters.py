# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
from decimal import Decimal

import trytond.tests.test_tryton
from trytond.pool import Pool
from trytond.tests.test_tryton import ModuleTestCase, with_transaction

from trytond.modules.company.tests import create_company, set_company
from trytond.modules.account.tests import create_chart


class TestCase(ModuleTestCase):
    'Test module'
    module = 'sale_subchapters'

    def create_sale(self, company, customer, payment_term):
        pool = Pool()
        Sale = pool.get('sale.sale')
        sale = Sale()
        sale.company = company
        sale.party = customer
        sale.invoice_address = customer.addresses[0]
        sale.shipment_address = customer.addresses[0]
        sale.currency = company.currency
        sale.payment_term = payment_term
        sale.invoice_method = 'order'
        sale.shipment_method = 'manual'
        sale.lines = []
        return sale

    def create_sale_line(self, sale, line_type, suffix=None):
        assert line_type in ('line', 'title', 'subtitle', 'subtotal',
            'subsubtotal')
        pool = Pool()
        SaleLine = pool.get('sale.line')
        sale_line = SaleLine()
        sale.lines = list(sale.lines) + [sale_line]
        sale_line.type = line_type
        if line_type == 'line':
            sale_line.quantity = 1
            sale_line.unit_price = 10
            sale_line.description = 'Normal line'
        elif line_type in ('title', 'subtitle'):
            sale_line.description = 'Title line'
        elif line_type in ('subtotal', 'subsubtotal'):
            sale_line.description = 'Subtotal line'
        if suffix:
            sale_line.description += suffix

    @with_transaction()
    def test0010subsubtotal_amount(self):
        'Test subsubtotal line amount'
        pool = Pool()
        Account = pool.get('account.account')
        Party = pool.get('party.party')
        PaymentTerm = pool.get('account.invoice.payment_term')

        # Create Company
        party = Party(name='Party')
        party.save()
        company = create_company()
        with set_company(company):

            # Create Chart of Accounts
            create_chart(company)
            receivable, = Account.search([('type.receivable', '=', True)])

            # Create Payment Term
            payment_term, = PaymentTerm.create([{
                        'name': 'Direct',
                        'lines': [('create', [{'type': 'remainder'}])]
                        }])

            customer, = Party.create([{
                        'name': 'customer',
                        'addresses': [
                            ('create', [{}]),
                            ],
                        'account_receivable': receivable.id,
                        'customer_payment_term': payment_term.id,
                        }])

            # Sale with 1 subtotal line
            sale1 = self.create_sale(company, customer, payment_term)
            self.create_sale_line(sale1, 'line')
            self.create_sale_line(sale1, 'line')
            self.create_sale_line(sale1, 'subtotal')
            self.create_sale_line(sale1, 'line')
            sale1.save()
            self.assertEqual(sale1.lines[-2].amount, Decimal('20'))

            # Sale with 1 subsubtotal line
            sale2 = self.create_sale(company, customer, payment_term)
            self.create_sale_line(sale2, 'line')
            self.create_sale_line(sale2, 'line')
            self.create_sale_line(sale2, 'subsubtotal')
            self.create_sale_line(sale2, 'line')
            sale2.save()
            self.assertEqual(sale2.lines[-2].amount, Decimal('20'))

            # Sale with 1 subsubtotal and 1 subtotal
            sale3 = self.create_sale(company, customer, payment_term)
            self.create_sale_line(sale3, 'line')
            self.create_sale_line(sale3, 'line')
            self.create_sale_line(sale3, 'subsubtotal')
            self.create_sale_line(sale3, 'line')
            self.create_sale_line(sale3, 'line')
            self.create_sale_line(sale3, 'subtotal')
            self.create_sale_line(sale3, 'line')
            sale3.save()
            self.assertEqual(sale3.lines[2].amount, Decimal('20'))
            self.assertEqual(sale3.lines[-2].amount, Decimal('40'))

            # Sale with 1 subtotal and 1 subsubtotal
            sale3 = self.create_sale(company, customer, payment_term)
            self.create_sale_line(sale3, 'line')
            self.create_sale_line(sale3, 'line')
            self.create_sale_line(sale3, 'subtotal')
            self.create_sale_line(sale3, 'line')
            self.create_sale_line(sale3, 'line')
            self.create_sale_line(sale3, 'subsubtotal')
            self.create_sale_line(sale3, 'line')
            sale3.save()
            self.assertEqual(sale3.lines[2].amount, Decimal('20'))
            self.assertEqual(sale3.lines[-2].amount, Decimal('20'))

            # Sale with some subtotals and subsubtotals
            sale4 = self.create_sale(company, customer, payment_term)
            self.create_sale_line(sale4, 'title')
            self.create_sale_line(sale4, 'subtitle')
            self.create_sale_line(sale4, 'line')
            self.create_sale_line(sale4, 'line')
            self.create_sale_line(sale4, 'subsubtotal')
            self.create_sale_line(sale4, 'subtitle')
            self.create_sale_line(sale4, 'line')
            self.create_sale_line(sale4, 'line')
            self.create_sale_line(sale4, 'line')
            self.create_sale_line(sale4, 'subsubtotal')
            self.create_sale_line(sale4, 'subtotal')
            self.create_sale_line(sale4, 'title')
            self.create_sale_line(sale4, 'subtitle')
            self.create_sale_line(sale4, 'line')
            self.create_sale_line(sale4, 'subsubtotal')
            self.create_sale_line(sale4, 'subtitle')
            self.create_sale_line(sale4, 'line')
            self.create_sale_line(sale4, 'line')
            self.create_sale_line(sale4, 'line')
            self.create_sale_line(sale4, 'line')
            self.create_sale_line(sale4, 'line')
            self.create_sale_line(sale4, 'subsubtotal')
            self.create_sale_line(sale4, 'subtotal')
            sale4.save()
            self.assertEqual(sale4.lines[4].amount, Decimal('20'))
            self.assertEqual(sale4.lines[9].amount, Decimal('30'))
            self.assertEqual(sale4.lines[10].amount, Decimal('50'))
            self.assertEqual(sale4.lines[14].amount, Decimal('10'))
            self.assertEqual(sale4.lines[-2].amount, Decimal('50'))
            self.assertEqual(sale4.lines[-1].amount, Decimal('60'))

    @with_transaction()
    def test0020update_subtotals(self):
        'Test update_subtotals'
        pool = Pool()
        Account = pool.get('account.account')
        Party = pool.get('party.party')
        PaymentTerm = pool.get('account.invoice.payment_term')
        Sale = pool.get('sale.sale')
        SaleLine = pool.get('sale.line')

        # Create Company
        party = Party(name='Party')
        party.save()
        company = create_company()
        with set_company(company):

            # Create Chart of Accounts
            create_chart(company)
            receivable, = Account.search([('type.receivable', '=', True)])

            # Create Payment Term
            payment_term, = PaymentTerm.create([{
                        'name': 'Direct',
                        'lines': [('create', [{'type': 'remainder'}])]
                        }])

            customer, = Party.create([{
                        'name': 'customer',
                        'addresses': [
                            ('create', [{}]),
                            ],
                        'account_receivable': receivable.id,
                        'customer_payment_term': payment_term.id,
                        }])

            def check_subtotal(sale, index, type_, suffix, amount):
                self.assertEqual(
                    (sale.lines[index].type, sale.lines[index].description,
                        sale.lines[index].amount),
                    (type_, 'Subtotal Title line%s' % suffix, amount))

            # Sale with some titles and subtitles
            sale1 = self.create_sale(company, customer, payment_term)
            self.create_sale_line(sale1, 'title', suffix=' A')
            self.create_sale_line(sale1, 'subtitle', suffix=' A.1')
            self.create_sale_line(sale1, 'line')
            self.create_sale_line(sale1, 'line')
            self.create_sale_line(sale1, 'subtitle', suffix=' A.2')
            self.create_sale_line(sale1, 'line')
            self.create_sale_line(sale1, 'line')
            self.create_sale_line(sale1, 'line')
            self.create_sale_line(sale1, 'title', suffix=' B')
            self.create_sale_line(sale1, 'line')
            sale1.save()
            self.assertEqual(len(sale1.lines), 10)

            Sale.update_subtotals([sale1])
            self.assertEqual(len(sale1.lines), 14)
            check_subtotal(sale1, 4, 'subsubtotal', ' A.1', Decimal('20.00'))
            check_subtotal(sale1, 9, 'subsubtotal', ' A.2', Decimal('30.00'))
            check_subtotal(sale1, 10, 'subtotal', ' A', Decimal('50.00'))
            check_subtotal(sale1, 13, 'subtotal', ' B', Decimal('10.00'))

            # Execute update_subtotals again and nothing changes
            Sale.update_subtotals([sale1])
            self.assertEqual(len(sale1.lines), 14)
            check_subtotal(sale1, 4, 'subsubtotal', ' A.1', Decimal('20.00'))
            check_subtotal(sale1, 9, 'subsubtotal', ' A.2', Decimal('30.00'))
            check_subtotal(sale1, 10, 'subtotal', ' A', Decimal('50.00'))
            check_subtotal(sale1, 13, 'subtotal', ' B', Decimal('10.00'))

            # Delete some subtotals and update them again
            SaleLine.delete([sale1.lines[4], sale1.lines[10]])
            self.assertEqual(len(sale1.lines), 12)
            Sale.update_subtotals([sale1])
            self.assertEqual(len(sale1.lines), 14)
            check_subtotal(sale1, 4, 'subsubtotal', ' A.1', Decimal('20.00'))
            check_subtotal(sale1, 9, 'subsubtotal', ' A.2', Decimal('30.00'))
            check_subtotal(sale1, 10, 'subtotal', ' A', Decimal('50.00'))
            check_subtotal(sale1, 13, 'subtotal', ' B', Decimal('10.00'))

            # Delete some subtotals and update them again
            SaleLine.delete([sale1.lines[9], sale1.lines[13]])
            self.assertEqual(len(sale1.lines), 12)
            Sale.update_subtotals([sale1])
            self.assertEqual(len(sale1.lines), 14)
            check_subtotal(sale1, 4, 'subsubtotal', ' A.1', Decimal('20.00'))
            check_subtotal(sale1, 9, 'subsubtotal', ' A.2', Decimal('30.00'))
            check_subtotal(sale1, 10, 'subtotal', ' A', Decimal('50.00'))
            check_subtotal(sale1, 13, 'subtotal', ' B', Decimal('10.00'))

            # Delete some subtotals and update them again
            SaleLine.delete([sale1.lines[4], sale1.lines[9]])
            self.assertEqual(len(sale1.lines), 12)
            Sale.update_subtotals([sale1])
            self.assertEqual(len(sale1.lines), 14)
            check_subtotal(sale1, 4, 'subsubtotal', ' A.1', Decimal('20.00'))
            check_subtotal(sale1, 9, 'subsubtotal', ' A.2', Decimal('30.00'))
            check_subtotal(sale1, 10, 'subtotal', ' A', Decimal('50.00'))
            check_subtotal(sale1, 13, 'subtotal', ' B', Decimal('10.00'))

            # Delete some subtotals and update them again
            SaleLine.delete([sale1.lines[10], sale1.lines[13]])
            self.assertEqual(len(sale1.lines), 12)
            Sale.update_subtotals([sale1])
            self.assertEqual(len(sale1.lines), 14)
            check_subtotal(sale1, 4, 'subsubtotal', ' A.1', Decimal('20.00'))
            check_subtotal(sale1, 9, 'subsubtotal', ' A.2', Decimal('30.00'))
            check_subtotal(sale1, 10, 'subtotal', ' A', Decimal('50.00'))
            check_subtotal(sale1, 13, 'subtotal', ' B', Decimal('10.00'))

            # Sale with lines standing alone mixed with titles
            sale2 = self.create_sale(company, customer, payment_term)
            self.create_sale_line(sale2, 'title', suffix=' A')
            self.create_sale_line(sale2, 'line')
            self.create_sale_line(sale2, 'title', suffix=' B')
            self.create_sale_line(sale2, 'line')
            self.create_sale_line(sale2, 'line')
            sale2.save()
            self.assertEqual(len(sale2.lines), 5)

            Sale.update_subtotals([sale2])
            check_subtotal(sale2, -5, 'subtotal', ' A', Decimal('10.00'))
            check_subtotal(sale2, -1, 'subtotal', ' B', Decimal('20.00'))

            # Sale with lines insede titles mixed with lines inside subtitles
            sale3 = self.create_sale(company, customer, payment_term)
            self.create_sale_line(sale3, 'title', suffix=' A')
            self.create_sale_line(sale3, 'line')
            self.create_sale_line(sale3, 'subtitle', suffix=' A.1')
            self.create_sale_line(sale3, 'line')
            self.create_sale_line(sale3, 'line')
            sale3.save()
            self.assertEqual(len(sale3.lines), 5)

            Sale.update_subtotals([sale3])
            check_subtotal(sale3, -2, 'subsubtotal', ' A.1', Decimal('20.00'))
            check_subtotal(sale3, -1, 'subtotal', ' A', Decimal('30.00'))

def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCase))
    return suite
