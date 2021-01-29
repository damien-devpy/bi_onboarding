# -*- coding: utf-8 -*-

# Copyright(C) 2021      Damien
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

from weboob.browser.elements import ItemElement, ListElement, TableElement, method
from weboob.browser.filters.standard import CleanDecimal, CleanText, Currency, Date, Field, Regexp
from weboob.browser.pages import HTMLPage, LoggedPage, pagination
from weboob.capabilities.bank import Account, Transaction
from weboob.exceptions import BrowserIncorrectPassword


class LoginPage(HTMLPage):

    def do_login(self, username, password):
        form = self.get_form()
        form['login'] = username
        form['password'] = password
        form.submit()

    def check_invalid_credentials(self):
        error_msg = CleanText('//div[@class="error"]')(self.doc)

        if 'Invalid login/password' in error_msg:
            raise BrowserIncorrectPassword(error_msg)

class AccountsPage(LoggedPage, HTMLPage):

    @method
    class iter_accounts(ListElement):
        item_xpath = '//table/tbody/tr'

        class item(ItemElement):
            klass = Account
            
            obj_id = Regexp(CleanText('./td/a'), r'\(([0-9A-Z]*)\)')
            obj_label = CleanText('./td/a')
            obj_balance = CleanDecimal.French('./td[2]')
            obj_currency = Currency('./td[2]')

class HistoryAccount(LoggedPage, HTMLPage):

    PAGINATION = '?page='

    @pagination
    @method
    class iter_history(ListElement):
        item_xpath = '//table/tbody/tr'

        def next_page(self):
            match = re.search(r'Page (\d)/(\d)', CleanText('.')(self))

            current = match.group(1)
            last = match.group(2)

            if int(current) < int(last):
                next_one = str(int(current) + 1)

                return self.page.url.replace(f"{self.page.PAGINATION}" + current, f"{self.page.PAGINATION}" + next_one)

        class item(ItemElement):
            klass = Transaction

            obj_date = Date(CleanText('./td[1]'))
            obj_label = CleanText('./td[2]')

            def obj_amount(self):
                return (
                    CleanDecimal.French('./td[3]', default=0)(self) +
                    CleanDecimal.French('./td[4]', default=0)(self)
                )









    

