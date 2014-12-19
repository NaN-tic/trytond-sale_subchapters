# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from decimal import Decimal

from trytond.pool import PoolMeta
from trytond.pyson import Eval

__all__ = ['SaleLine']
__metaclass__ = PoolMeta

_ZERO = Decimal('0.0')


class SaleLine:
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
            if line2.type == 'line':
                subsubtotal += line2.sale.currency.round(
                    Decimal(str(line2.quantity)) * line2.unit_price)
            elif line2.type in ('subtotal', 'subsubtotal'):
                if self == line2:
                    break
                subsubtotal = _ZERO
        return subsubtotal
