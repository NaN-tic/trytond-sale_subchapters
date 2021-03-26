# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from decimal import Decimal

from trytond.model import ModelView
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.i18n import gettext

__all__ = ['Sale', 'SaleLine']

_ZERO = Decimal('0.0')


class Sale(metaclass=PoolMeta):
    __name__ = 'sale.sale'

    @classmethod
    def __setup__(cls):
        super(Sale, cls).__setup__()
        cls._buttons.update({
                'update_subtotals': {
                    'invisible': Eval('state') != 'draft',
                    'readonly': ~Eval('lines', []),
                    'icon': 'tryton-refresh',
                    },
                })

    @classmethod
    @ModelView.button
    def update_subtotals(cls, sales):
        pool = Pool()
        SaleLine = pool.get('sale.line')

        to_create = []
        for sale in sales:
            title = subtitle = None
            sequence = 1
            for line in sale.lines:
                if line.type == 'subsubtotal':
                    subtitle = None
                elif line.type in ('subtotal', 'subtitle', 'title'):
                    if subtitle:
                        to_create.append(
                            subtitle.get_subtotal(sequence)._save_values)
                        sequence += 1
                    if line.type == 'subtotal':
                        title = subtitle = None
                    elif line.type == 'subtitle':
                        subtitle = line
                    elif line.type == 'title':
                        if title:
                            to_create.append(
                                title.get_subtotal(sequence)._save_values)
                            sequence += 1
                        title = line
                        subtitle = None
                if line.sequence != sequence:
                    line.sequence = sequence
                    line.save()
                sequence += 1
            if subtitle:
                to_create.append(
                    subtitle.get_subtotal(sequence)._save_values)
                sequence += 1
            if title:
                to_create.append(
                    title.get_subtotal(sequence)._save_values)
        if to_create:
            SaleLine.create(to_create)


class SaleLine(metaclass=PoolMeta):
    __name__ = 'sale.line'

    @classmethod
    def __setup__(cls):
        super(SaleLine, cls).__setup__()
        for item in (('subsubtotal', 'Subsubtotal'), ('subtitle', 'Subtitle')):
            if item not in cls.type.selection:
                cls.type.selection.append(item)
        cls.amount.states['invisible'] &= (Eval('type') != 'subsubtotal')

    def get_amount(self, name):
        if self.type != 'subsubtotal':
            return super(SaleLine, self).get_amount(name)
        subsubtotal = _ZERO
        for line2 in self.sale.lines:
            if line2.type in ['title','subtitle']:
                subsubtotal = _ZERO
            if line2.type in ['comment']:
                continue
            if line2.type == 'line':
                subsubtotal += line2.sale.currency.round(
                    Decimal(str(line2.quantity)) * line2.unit_price)
            elif line2.type in ('subtotal', 'subsubtotal'):
                if self == line2:
                    break
                subsubtotal = _ZERO
        return subsubtotal

    def get_subtotal(self, sequence):
        Line = Pool().get('sale.line')
        type_ = 'subtotal' if self.type == 'title' else 'subsubtotal'
        prefix = gettext('sale_subchapters.subtotal_prefix')
        return Line(
            sale=self.sale,
            sequence=sequence,
            type=type_,
            description='%s %s' % (prefix, self.description),
            )
