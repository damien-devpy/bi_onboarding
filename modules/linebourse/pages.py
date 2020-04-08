# -*- coding: utf-8 -*-

# Copyright(C) 2017      Vincent Ardisson
#
# This file is part of a weboob module.
#
# This weboob module is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This weboob module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this weboob module. If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import re

from weboob.browser.pages import HTMLPage, LoggedPage
from weboob.browser.elements import method, TableElement, ItemElement
from weboob.browser.filters.standard import (
    CleanText, Date, CleanDecimal, Regexp, Eval, Field
)
from weboob.browser.filters.html import TableCell
from weboob.capabilities.base import NotAvailable
from weboob.capabilities.wealth import Investment
from weboob.tools.capabilities.bank.transactions import FrenchTransaction as Transaction
from weboob.tools.capabilities.bank.investments import create_french_liquidity, IsinCode, IsinType
from weboob.tools.compat import quote_plus
from weboob.exceptions import ActionNeeded


def MyDecimal(*args, **kwargs):
    kwargs['replace_dots'] = True
    return CleanDecimal(*args, **kwargs)


class MainPage(LoggedPage, HTMLPage):
    pass


class FirstConnectionPage(LoggedPage, HTMLPage):
    def on_load(self):
        raise ActionNeeded(CleanText('//p[contains(text(), "prendre connaissance")]')(self.doc))


class AccountPage(LoggedPage, HTMLPage):
    def is_on_right_portfolio(self, account_id):
        return len(self.doc.xpath('//form[@class="choixCompte"]//option[@selected and contains(text(), $id)]', id=account_id))

    def get_compte(self, account_id):
        values = self.doc.xpath('//option[contains(text(), $id)]/@value', id=account_id)
        assert len(values) == 1, 'could not find account %r' % account_id

        return quote_plus(values[0])


class HistoryPage(AccountPage):
    def get_periods(self):
        return list(self.doc.xpath('//select[@id="ListeDate"]/option/@value'))

    @method
    class iter_history(TableElement):
        col_date = 'Date'
        col_name = 'Valeur'
        col_quantity = u'Quantité'
        col_amount = u'Montant net EUR'
        col_label = u'Opération'

        head_xpath = u'//table[@summary="Historique operations"]//tr[th]/th'
        item_xpath = u'//table[@summary="Historique operations"]//tr[not(th)]'

        def parse(self, el):
            self.labels = {}

        class item(ItemElement):
            def condition(self):
                text = CleanText('td')(self)
                return not text.startswith('Aucune information disponible')

            klass = Transaction

            obj_date = Date(CleanText(TableCell('date')), dayfirst=True)
            obj_amount = MyDecimal(TableCell('amount'))
            obj_raw = CleanText(TableCell('label'))

            def obj_investments(self):
                inv = Investment()
                inv.quantity = CleanDecimal(TableCell('quantity'), replace_dots=True)(self)
                inv.code_type = Investment.CODE_TYPE_ISIN

                txt = CleanText(TableCell('name'))(self)
                match = re.match('(?:(.*) )?- ([^-]+)$', txt)
                inv.label = match.group(1) or NotAvailable
                inv.code = match.group(2)

                if inv.code in self.parent.labels:
                    inv.label = inv.label or self.parent.labels[inv.code]
                elif inv.label:
                    self.parent.labels[inv.code] = inv.label
                else:
                    inv.label = inv.code

                return [inv]


class InvestmentPage(AccountPage):
    @method
    class iter_investments(TableElement):
        col_label = 'Valeur'
        col_quantity = u'Quantité'
        col_valuation = u'Valorisation EUR'
        col_unitvalue = 'Cours/VL'
        col_unitprice = 'Prix moyen EUR'
        col_portfolio_share = '% Actif'
        col_diff = u'+/- value latente EUR'

        head_xpath = u'//table[starts-with(@summary,"Contenu du portefeuille")]/thead//th'
        item_xpath = u'//table[starts-with(@summary,"Contenu du portefeuille")]/tbody/tr[2]'

        class item(ItemElement):
            klass = Investment

            def condition(self):
                return Field('quantity')(self) != NotAvailable and Field('quantity')(self) > 0

            obj_quantity = MyDecimal(TableCell('quantity'), default=NotAvailable)
            obj_unitvalue = MyDecimal(TableCell('unitvalue'), default=NotAvailable)
            obj_unitprice = MyDecimal(TableCell('unitprice'), default=NotAvailable)
            obj_valuation = MyDecimal(TableCell('valuation'), default=NotAvailable)
            obj_portfolio_share = Eval(lambda x: x / 100 if x else NotAvailable, MyDecimal(TableCell('portfolio_share'), default=NotAvailable))
            obj_diff = MyDecimal(TableCell('diff', default=NotAvailable), default=NotAvailable)
            obj_label = CleanText(Regexp(CleanText('./preceding-sibling::tr/td[1]'), r'(.*)- .*'))

            obj_code = IsinCode(Regexp(CleanText('./preceding-sibling::tr/td[1]'), r'- ([^\s]*)'), default=NotAvailable)
            obj_code_type = IsinType(Regexp(CleanText('./preceding-sibling::tr/td[1]'), r'- ([^\s]*)'), default=NotAvailable)

    # Only used by bp modules since others quality websites provide another account with the liquidities
    def get_liquidity(self):
        liquidity = CleanDecimal('//table//tr[@class="titreAvant"]/td[contains(text(), "Liquidit")]/following-sibling::td', replace_dots=True)(self.doc)
        if liquidity:
            return create_french_liquidity(liquidity)


class MessagePage(LoggedPage, HTMLPage):
    def get_message(self):
        # If the message has a box that must be checked to get to go further,
        # we fetch the title of the information message.
        if CleanText('//label[@for="signature1"]')(self.doc):
            return CleanText('//form//p[@class="bold"]')(self.doc)

    def submit(self):
        # taken from linebourse implementation in caissedepargne module
        form = self.get_form(name='leForm')
        form['signatur1'] = 'on'
        form.submit()


class BrokenPage(LoggedPage, HTMLPage):
    pass
