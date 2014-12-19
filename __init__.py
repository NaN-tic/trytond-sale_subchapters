# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .sale import SaleLine

def register():
    Pool.register(
        SaleLine,
        module='sale_subchapters', type_='model')
