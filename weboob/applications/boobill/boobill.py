# -*- coding: utf-8 -*-

# Copyright(C) 2012-2013 Florent Fourcot
#
# This file is part of weboob.
#
# weboob is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# weboob is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with weboob. If not, see <http://www.gnu.org/licenses/>.


import sys
from decimal import Decimal

from weboob.capabilities.bill import ICapBill, Detail, Subscription
from weboob.tools.application.repl import ReplApplication
from weboob.tools.application.formatters.iformatter import PrettyFormatter


__all__ = ['Boobill']


class SubscriptionsFormatter(PrettyFormatter):
    MANDATORY_FIELDS = ('id', 'label')

    def get_title(self, obj):
        if obj.renewdate:
            return u"%s - %s" % (obj.label, obj.renewdate.strftime('%d/%m/%y'))
        return obj.label


class Boobill(ReplApplication):
    APPNAME = 'boobill'
    VERSION = '0.g'
    COPYRIGHT = 'Copyright(C) 2012 Florent Fourcot'
    DESCRIPTION = 'Console application allowing to get and download bills.'
    SHORT_DESCRIPTION = "get and download bills"
    CAPS = ICapBill
    COLLECTION_OBJECTS = (Subscription, )
    EXTRA_FORMATTERS = {'subscriptions':   SubscriptionsFormatter,
                        }
    DEFAULT_FORMATTER = 'table'
    COMMANDS_FORMATTERS = {'subscriptions':   'subscriptions',
                           'ls':              'subscriptions',
                          }

    def main(self, argv):
        self.load_config()
        return ReplApplication.main(self, argv)

    def exec_method(self, id, method):
        l = []
        id, backend_name = self.parse_id(id)

        if not id:
            for subscrib in self.get_object_list('iter_subscription'):
                l.append((subscrib.id, subscrib.backend))
        else:
            l.append((id, backend_name))

        for id, backend in l:
            names = (backend,) if backend is not None else None

            self.start_format()
            for backend, result in self.do(method, id, backends=names):
                self.format(result)
            self.flush()

    def do_subscriptions(self, line):
        """
        subscriptions

        List subscriptions
        """
        self.start_format()
        for subscription in self.get_object_list('iter_subscription'):
            self.format(subscription)
        self.flush()

    def do_details(self, id):
        """
        details [ID]

        Get details of subscriptions.
        If no ID given, display all details of all backends
        """
        l = []
        id, backend_name = self.parse_id(id)

        if not id:
            for subscrib in self.get_object_list('iter_subscription'):
                l.append((subscrib.id, subscrib.backend))
        else:
            l.append((id, backend_name))

        for id, backend in l:
            names = (backend,) if backend is not None else None
            # XXX: should be generated by backend? -Flo
            # XXX: no, but you should do it in a specific formatter -romain
            mysum = Detail()
            mysum.label = u"Sum"
            mysum.infos = u"Generated by boobill"
            mysum.price = Decimal("0.")

            self.start_format()
            for backend, detail in self.do('get_details', id, backends=names):
                self.format(detail)
                mysum.price = detail.price + mysum.price

            self.format(mysum)
            self.flush()

    def do_balance(self, id):
        """
        balance [Id]

        Get balance of subscriptions.
        If no ID given, display balance of all backends
        """

        self.exec_method(id, 'get_balance')

    def do_history(self, id):
        """
        history [Id]

        Get the history of subscriptions.
        If no ID given, display histories of all backends
        """
        self.exec_method(id, 'iter_bills_history')

    def do_bills(self, id):
        """
        bills [Id]

        Get the list of bills documents for subscriptions.
        If no ID given, display bills of all backends
        """
        self.exec_method(id, 'iter_bills')

    def do_download(self, line):
        """
        download [Id | all] [FILENAME]

        download Id [FILENAME]

        download the bill
        id is the identifier of the bill (hint: try bills command)
        FILENAME is where to write the file. If FILENAME is '-',
        the file is written to stdout.

        download all [Id]

        You can use special word "all" and download all bills of
        subscription identified by Id.
        If Id not given, download bills of all subscriptions.
        """
        id, dest = self.parse_command_args(line, 2, 1)
        id, backend_name = self.parse_id(id)
        if not id:
            print >>sys.stderr, 'Error: please give a bill ID (hint: use bills command)'
            return 2

        names = (backend_name,) if backend_name is not None else None
        # Special keywords, download all bills of all subscriptions
        if id == "all":
            if dest is None:
                for backend, subscription in self.do('iter_subscription', backends=names):
                    self.download_all(subscription.id, names)
                return
            else:
                self.download_all(dest, names)
                return

        if dest is None:
            for backend, bill in self.do('get_bill', id, backends=names):
                dest = id + "." + bill.format

        for backend, buf in self.do('download_bill', id, backends=names):
            if buf:
                if dest == "-":
                    print buf
                else:
                    try:
                        with open(dest, 'w') as f:
                            f.write(buf)
                    except IOError, e:
                        print >>sys.stderr, 'Unable to write bill in "%s": %s' % (dest, e)
                        return 1
                return

    def download_all(self, id, names):
        id, backend_name = self.parse_id(id)
        for backend, bill in self.do('iter_bills', id, backends=names):
            dest = bill.id + "." + bill.format
            for backend2, buf in self.do('download_bill', bill.id, backends=names):
                if buf:
                    if dest == "-":
                        print buf
                    else:
                        try:
                            with open(dest, 'w') as f:
                                f.write(buf)
                        except IOError, e:
                            print >>sys.stderr, 'Unable to write bill in "%s": %s' % (dest, e)
                            return 1

        return
