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

            def create_sale():
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

            def create_sale_line(sale, line_type):
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

            # Sale with 1 subtotal line
            sale1 = create_sale()
            create_sale_line(sale1, 'line')
            create_sale_line(sale1, 'line')
            create_sale_line(sale1, 'subtotal')
            create_sale_line(sale1, 'line')
            sale1.save()
            self.assertEqual(sale1.lines[-2].amount, Decimal('20'))

            # Sale with 1 subsubtotal line
            sale2 = create_sale()
            create_sale_line(sale2, 'line')
            create_sale_line(sale2, 'line')
            create_sale_line(sale2, 'subsubtotal')
            create_sale_line(sale2, 'line')
            sale2.save()
            self.assertEqual(sale2.lines[-2].amount, Decimal('20'))

            # Sale with 1 subsubtotal and 1 subtotal
            sale3 = create_sale()
            create_sale_line(sale3, 'line')
            create_sale_line(sale3, 'line')
            create_sale_line(sale3, 'subsubtotal')
            create_sale_line(sale3, 'line')
            create_sale_line(sale3, 'line')
            create_sale_line(sale3, 'subtotal')
            create_sale_line(sale3, 'line')
            sale3.save()
            self.assertEqual(sale3.lines[2].amount, Decimal('20'))
            self.assertEqual(sale3.lines[-2].amount, Decimal('40'))

            # Sale with 1 subtotal and 1 subsubtotal
            sale3 = create_sale()
            create_sale_line(sale3, 'line')
            create_sale_line(sale3, 'line')
            create_sale_line(sale3, 'subtotal')
            create_sale_line(sale3, 'line')
            create_sale_line(sale3, 'line')
            create_sale_line(sale3, 'subsubtotal')
            create_sale_line(sale3, 'line')
            sale3.save()
            self.assertEqual(sale3.lines[2].amount, Decimal('20'))
            self.assertEqual(sale3.lines[-2].amount, Decimal('20'))

            # Sale with some subtotals and subsubtotals
            sale4 = create_sale()
            create_sale_line(sale4, 'title')
            create_sale_line(sale4, 'subtitle')
            create_sale_line(sale4, 'line')
            create_sale_line(sale4, 'line')
            create_sale_line(sale4, 'subsubtotal')
            create_sale_line(sale4, 'subtitle')
            create_sale_line(sale4, 'line')
            create_sale_line(sale4, 'line')
            create_sale_line(sale4, 'line')
            create_sale_line(sale4, 'subsubtotal')
            create_sale_line(sale4, 'subtotal')
            create_sale_line(sale4, 'title')
            create_sale_line(sale4, 'subtitle')
            create_sale_line(sale4, 'line')
            create_sale_line(sale4, 'subsubtotal')
            create_sale_line(sale4, 'subtitle')
            create_sale_line(sale4, 'line')
            create_sale_line(sale4, 'line')
            create_sale_line(sale4, 'line')
            create_sale_line(sale4, 'line')
            create_sale_line(sale4, 'line')
            create_sale_line(sale4, 'subsubtotal')
            create_sale_line(sale4, 'subtotal')
            sale4.save()
            self.assertEqual(sale4.lines[4].amount, Decimal('20'))
            self.assertEqual(sale4.lines[9].amount, Decimal('30'))
            self.assertEqual(sale4.lines[10].amount, Decimal('50'))
            self.assertEqual(sale4.lines[14].amount, Decimal('10'))
            self.assertEqual(sale4.lines[-2].amount, Decimal('50'))
            self.assertEqual(sale4.lines[-1].amount, Decimal('60'))


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
