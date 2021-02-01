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

from weboob.browser.elements import DictElement, ItemElement, ListElement, method
from weboob.browser.filters.json import Dict
from weboob.browser.filters.standard import CleanDecimal, CleanText
from weboob.browser.pages import JsonPage, LoggedPage
from weboob.capabilities.account import Account


class LoginPage(JsonPage):
    pass

class AccountsPage(LoggedPage, JsonPage):

    @method
    class iter_accounts(DictElement):
        item_xpath = 'accounts'
    
        class item(ItemElement):

            obj_id = CleanText(Dict('id'))
            obj_label = CleanText(Dict('label'))
            obj_balance = CleanDecimal(Dict('balance'))

