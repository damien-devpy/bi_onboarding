# -*- coding: utf-8 -*-

# Copyright(C) 2010-2012 Julien Veyssier
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

from weboob.browser.elements import ItemElement, method, TableElement
from weboob.browser.filters.html import Link
from weboob.browser.filters.standard import (
    CleanText, CleanDecimal, Currency, Env, TableCell, Field, Format, Base,
)
from weboob.browser.pages import AbstractPage, LoggedPage, HTMLPage
from weboob.capabilities.bank import Account
from weboob.capabilities.wealth import Investment
from weboob.capabilities.base import NotAvailable
from weboob.exceptions import ActionNeeded
from weboob.tools.capabilities.bank.investments import IsinCode, IsinType


class LoginPage(AbstractPage):
    PARENT = 'creditmutuel'
    PARENT_URL = 'login'


class PorPage(AbstractPage):
    PARENT = 'creditmutuel'
    PARENT_URL = 'por'

    def on_load(self):
        # info page, appearing every 30 min
        # we can bypass without asking to never show it again
        # parent module still uses the old portfolio PorPage which was removed from CIC
        if (
            self.doc.xpath('//form[contains(@action, "MsgCommerciaux")]') and
            self.doc.xpath('//input[contains(@id, "Valider")]') and
            'Pensez à activer Confirmation Mobile' in CleanText('//div[@id="divMessage"]/p[1]')(self.doc)
        ):
            if self.doc.xpath('//input[contains(@id, "chxOption")]'):  # "Ne plus afficher ce message" checkbox
                self.logger.info('Skipping message on PorPage')
                form = self.get_form(id='frmMere')
                form.submit()
            else:
                raise ActionNeeded(CleanText('//div[@id="divMessage"]/p[1]')(self.doc))

    def add_por_accounts(self, accounts):
        for por_account in self.iter_por_accounts():
            for account in accounts:
                # we update accounts that were already fetched
                if account.id.startswith(por_account.id) and not account.balance:
                    account._is_inv = por_account._is_inv
                    account.balance = por_account.balance
                    account.currency = por_account.currency
                    account.valuation_diff = por_account.valuation_diff
                    account.valuation_diff_ratio = por_account.valuation_diff_ratio
                    account.type = por_account.type
                    account.url = por_account.url
                    break
            else:
                accounts.append(por_account)

    @method
    class iter_por_accounts(TableElement):
        item_xpath = '//table[@id="tabSYNT"]//tr[td]'
        head_xpath = '//table[@id="tabSYNT"]//th'

        col_raw_label = 'Portefeuille'
        col_balance = re.compile(r'Valorisation en .*')
        col_valuation_diff = re.compile(r'\+/- Value latente en [^%].*')
        col_valuation_diff_ratio = re.compile(r'\+/- Value latente en %.*')

        class item(ItemElement):
            klass = Account

            def condition(self):
                self.env['id'] = CleanText('.//a', replace=[(' ', '')])(self)
                self.env['balance'] = CleanDecimal.French(TableCell('balance'), default=None)(self)
                is_global_view = Env('id')(self) == 'Vueconsolidée'
                has_empty_balance = Env('balance')(self) is None
                return not is_global_view and not has_empty_balance

            # These values are defined for other types of accounts
            obj__card_number = obj__link_id = None

            obj__is_inv = True

            # IDs on the old page were differentiated with 5 digits in front of the ID, but not here.
            # We still need to differentiate them so we add ".1" at the end.
            obj_id = Format('%s.1', Env('id'))

            def obj_label(self):
                # There is a link in the cell but we only want the text outside the 'a' tag
                return CleanText('./text()')(TableCell('raw_label')(self)[0])

            obj_balance = Env('balance')
            obj_currency = Currency(CleanText('//table[@id="tabSYNT"]/thead//span'), default=NotAvailable)

            obj_valuation_diff = CleanDecimal.French(TableCell('valuation_diff'), default=NotAvailable)

            obj__link_inv = Link('.//a', default=NotAvailable)

            def obj_type(self):
                return self.page.get_type(Field('label')(self))

            def obj_valuation_diff_ratio(self):
                valuation_diff_ratio_percent = CleanDecimal.French(TableCell('valuation_diff_ratio'), default=NotAvailable)(self)
                if valuation_diff_ratio_percent:
                    return valuation_diff_ratio_percent / 100
                return NotAvailable

    def send_form(self, account):
        # Not a form anymore but we keep the parent's behavior
        self.browser.location(account._link_inv)


class InvestmentDetailsPage(LoggedPage, HTMLPage):
    @method
    class iter_investment(TableElement):
        item_xpath = '//table[@id="tabValorisation"]/tbody/tr[td]'
        head_xpath = '//table[@id="tabValorisation"]/thead//th'

        # Several columns contain two values in the same cell, in two distinct 'div'
        col_label = 'Valeur'  # label & code
        col_quantity = 'Quantité / Montant nominal'
        col_unitvalue = re.compile(r'Cours.*')  # unitvalue & unitprice
        col_valuation = re.compile(r'Valorisation.*')  # valuation & portfolio_share
        col_diff = re.compile(r'\+/- Value latente.*')  # diff & diff_ratio

        class item(ItemElement):
            klass = Investment

            def condition(self):
                # Some invests have 'NB' as their valuation, we filter them out.
                return Base(TableCell('valuation'), CleanDecimal.French('./div[1]', default=None))(self) is not None

            obj_quantity = CleanDecimal.French(TableCell('quantity'))
            obj_label = Base(TableCell('label'), CleanText('./div[1]'))
            obj_code = Base(TableCell('label'), IsinCode(CleanText('./div[2]'), default=NotAvailable))
            obj_code_type = Base(TableCell('label'), IsinType(CleanText('./div[2]'), default=NotAvailable))

            obj_original_currency = Base(TableCell('unitvalue'), Currency('./div[1]', default=NotAvailable))

            def obj_unitvalue(self):
                # The unit value is given in the original currency.
                # All other values are in the account currency.
                if Field('original_currency')(self):
                    return NotAvailable

                # Sometimes we're given a ratio instead of the unit value.
                if '%' in Base(TableCell('unitvalue'), CleanText('./div[1]'))(self):
                    return NotAvailable
                return Base(TableCell('unitvalue'), CleanDecimal.French('./div[1]', default=NotAvailable))(self)

            def obj_original_unitvalue(self):
                if not Field('original_currency')(self):
                    return NotAvailable
                return Base(TableCell('unitvalue'), CleanDecimal.French('./div[1]', default=NotAvailable))(self)

            obj_unitprice = Base(TableCell('unitvalue'), CleanDecimal.French('./div[2]', default=NotAvailable))
            obj_valuation = Base(TableCell('valuation'), CleanDecimal.French('./div[1]'))
            obj_diff = Base(TableCell('diff'), CleanDecimal.French('./div[1]', default=NotAvailable))

            def obj_portfolio_share(self):
                portfolio_share_percent = Base(TableCell('valuation'), CleanDecimal.French('./div[2]', default=None))(self)
                if portfolio_share_percent:
                    return portfolio_share_percent / 100
                return NotAvailable

            def obj_diff_ratio(self):
                diff_ratio_percent = Base(TableCell('diff'), CleanDecimal.French('./div[2]', default=None))(self)
                if diff_ratio_percent:
                    return diff_ratio_percent / 100
                return NotAvailable


class DecoupledStatePage(AbstractPage):
    PARENT = 'creditmutuel'
    PARENT_URL = 'decoupled_state'
    BROWSER_ATTR = 'package.browser.CreditMutuelBrowser'


class CancelDecoupled(AbstractPage):
    PARENT = 'creditmutuel'
    PARENT_URL = 'cancel_decoupled'
    BROWSER_ATTR = 'package.browser.CreditMutuelBrowser'
