# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import doctest
import unittest
from decimal import Decimal

import trytond.tests.test_tryton
from trytond.tests.test_tryton import test_depends
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT
from trytond.transaction import Transaction


class TestCase(unittest.TestCase):
    'Test module'

    def setUp(self):
        trytond.tests.test_tryton.install_module('sale_subchapters')
        self.account = POOL.get('account.account')
        self.company = POOL.get('company.company')
        self.sale = POOL.get('sale.sale')
        self.sale_line = POOL.get('sale.line')
        self.party = POOL.get('party.party')
        self.payment_term = POOL.get('account.invoice.payment_term')
        self.user = POOL.get('res.user')

    def test0006depends(self):
        'Test depends'
        test_depends()

    def create_sale(self, company, customer, payment_term):
        sale = self.sale()
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
        sale_line = self.sale_line()
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

    def test0010subsubtotal_amount(self):
        'Test subsubtotal line amount'
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            company, = self.company.search([
                    ('rec_name', '=', 'Dunder Mifflin'),
                    ])
            self.user.write([self.user(USER)], {
                'main_company': company.id,
                'company': company.id,
                })

            receivable, = self.account.search([
                ('kind', '=', 'receivable'),
                ('company', '=', company.id),
                ])
            payment_term, = self.payment_term.create([{
                        'name': 'Payment Term',
                        'lines': [
                            ('create', [{
                                        'sequence': 0,
                                        'type': 'remainder',
                                        'months': 0,
                                        'days': 0,
                                        }])]
                        }])
            customer, = self.party.create([{
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

    def test0020update_subtotals(self):
        'Test update_subtotals'
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            company, = self.company.search([
                    ('rec_name', '=', 'Dunder Mifflin'),
                    ])
            self.user.write([self.user(USER)], {
                'main_company': company.id,
                'company': company.id,
                })

            receivable, = self.account.search([
                ('kind', '=', 'receivable'),
                ('company', '=', company.id),
                ])
            payment_term, = self.payment_term.create([{
                        'name': 'Payment Term',
                        'lines': [
                            ('create', [{
                                        'sequence': 0,
                                        'type': 'remainder',
                                        'months': 0,
                                        'days': 0,
                                        }])]
                        }])
            customer, = self.party.create([{
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

            self.sale.update_subtotals([sale1])
            self.assertEqual(len(sale1.lines), 14)
            check_subtotal(sale1, 4, 'subsubtotal', ' A.1', Decimal('20.00'))
            check_subtotal(sale1, 9, 'subsubtotal', ' A.2', Decimal('30.00'))
            check_subtotal(sale1, 10, 'subtotal', ' A', Decimal('50.00'))
            check_subtotal(sale1, 13, 'subtotal', ' B', Decimal('10.00'))

            # Execute update_subtotals again and nothing changes
            self.sale.update_subtotals([sale1])
            self.assertEqual(len(sale1.lines), 14)
            check_subtotal(sale1, 4, 'subsubtotal', ' A.1', Decimal('20.00'))
            check_subtotal(sale1, 9, 'subsubtotal', ' A.2', Decimal('30.00'))
            check_subtotal(sale1, 10, 'subtotal', ' A', Decimal('50.00'))
            check_subtotal(sale1, 13, 'subtotal', ' B', Decimal('10.00'))

            # Delete some subtotals and update them again
            self.sale_line.delete([sale1.lines[4], sale1.lines[10]])
            self.assertEqual(len(sale1.lines), 12)
            self.sale.update_subtotals([sale1])
            self.assertEqual(len(sale1.lines), 14)
            check_subtotal(sale1, 4, 'subsubtotal', ' A.1', Decimal('20.00'))
            check_subtotal(sale1, 9, 'subsubtotal', ' A.2', Decimal('30.00'))
            check_subtotal(sale1, 10, 'subtotal', ' A', Decimal('50.00'))
            check_subtotal(sale1, 13, 'subtotal', ' B', Decimal('10.00'))

            # Delete some subtotals and update them again
            self.sale_line.delete([sale1.lines[9], sale1.lines[13]])
            self.assertEqual(len(sale1.lines), 12)
            self.sale.update_subtotals([sale1])
            self.assertEqual(len(sale1.lines), 14)
            check_subtotal(sale1, 4, 'subsubtotal', ' A.1', Decimal('20.00'))
            check_subtotal(sale1, 9, 'subsubtotal', ' A.2', Decimal('30.00'))
            check_subtotal(sale1, 10, 'subtotal', ' A', Decimal('50.00'))
            check_subtotal(sale1, 13, 'subtotal', ' B', Decimal('10.00'))

            # Delete some subtotals and update them again
            self.sale_line.delete([sale1.lines[4], sale1.lines[9]])
            self.assertEqual(len(sale1.lines), 12)
            self.sale.update_subtotals([sale1])
            self.assertEqual(len(sale1.lines), 14)
            check_subtotal(sale1, 4, 'subsubtotal', ' A.1', Decimal('20.00'))
            check_subtotal(sale1, 9, 'subsubtotal', ' A.2', Decimal('30.00'))
            check_subtotal(sale1, 10, 'subtotal', ' A', Decimal('50.00'))
            check_subtotal(sale1, 13, 'subtotal', ' B', Decimal('10.00'))

            # Delete some subtotals and update them again
            self.sale_line.delete([sale1.lines[10], sale1.lines[13]])
            self.assertEqual(len(sale1.lines), 12)
            self.sale.update_subtotals([sale1])
            self.assertEqual(len(sale1.lines), 14)
            check_subtotal(sale1, 4, 'subsubtotal', ' A.1', Decimal('20.00'))
            check_subtotal(sale1, 9, 'subsubtotal', ' A.2', Decimal('30.00'))
            check_subtotal(sale1, 10, 'subtotal', ' A', Decimal('50.00'))
            check_subtotal(sale1, 13, 'subtotal', ' B', Decimal('10.00'))


def suite():
    suite = trytond.tests.test_tryton.suite()
    from trytond.modules.company.tests import test_company
    for test in test_company.suite():
        if test not in suite:
            suite.addTest(test)
    from trytond.modules.account.tests import test_account
    for test in test_account.suite():
        if test not in suite and not isinstance(test, doctest.DocTestCase):
            suite.addTest(test)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCase))
    return suite
