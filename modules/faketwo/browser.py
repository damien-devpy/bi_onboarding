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
from weboob.browser.exceptions import ClientError
from weboob.exceptions import BrowserIncorrectPassword, BrowserHTTPError
from .pages import LoginPage, AccountsPage


class FaketwoBrowser(LoginBrowser):
    BASEURL = 'https://people.lan.budget-insight.com/~ntome/fake_bank.wsgi/v2/'

    login = URL(r'login.json', LoginPage)
    accounts = URL(r'accounts.json', AccountsPage)

    def do_login(self):
        try:
            self.login.go(data={'login': self.username, 'password': self.password})
        except ClientError as err:
            if err.response.status_code == '401':
                raise BrowserIncorrectPassword(err)
            else:
                raise BrowserHTTPError(err)

    @need_login
    def iter_accounts(self):
        self.accounts.go()

    
