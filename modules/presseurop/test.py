# -*- coding: utf-8 -*-

# Copyright(C) 2012 Florent Fourcot
#
# This file is part of a weboob module.
#
# This weboob module is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This weboob module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this weboob module. If not, see <http://www.gnu.org/licenses/>.


from weboob.tools.test import BackendTest
from weboob.tools.value import Value


class PresseuropTest(BackendTest):
    MODULE = 'presseurop'

    def setUp(self):
        if not self.is_backend_configured():
            self.backend.config['lang'] = Value(value='fr')

    def test_new_messages(self):
        for message in self.backend.iter_unread_messages():
            pass
