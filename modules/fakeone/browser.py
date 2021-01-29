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


from weboob.browser import LoginBrowser, URL, need_login
from .pages import LoginPage, AccountsPage, HistoryAccount
import pdb

class FakeoneBrowser(LoginBrowser):
    BASEURL = 'https://people.lan.budget-insight.com/~ntome/fake_bank.wsgi/v1/'

    login = URL(r'login', LoginPage)
    history_account = URL(r'accounts/(?P<account_id>.*)\?page=(?P<page_id>[0-9]*)', HistoryAccount)
    accounts = URL(r'accounts', AccountsPage)

    def do_login(self):
        self.login.go()
        self.page.do_login(self.username, self.password)

        if self.login.is_here():
            self.page.check_invalid_credentials()

    @need_login
    def iter_accounts(self):
        self.accounts.go()
        return self.page.iter_accounts()

    @need_login
    def iter_history(self, account):
        self.history_account.go(account_id=account.id, page_id=1)
        return self.page.iter_history()
