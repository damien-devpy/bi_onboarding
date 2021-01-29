from modules.fakeone.browser import FakeoneBrowser
from modules.fakeone.pages import AccountsPage, HistoryAccount


class MockResponseAccount:

    def __init__(self, *args, **kwargs):
        self.url = 'http://random-url.com'
        self.content = b'''<html>
        <body>
        <table>
        <tbody>
            <tr>
                <td><a href="">Account (N0001)</a></td>
                <td>+42,00 \xe2\x82\xac</td>
            </tr>
            <tr>
                <td><a href="">Account (N0002)</a></td>
                <td>+4 242,00 \xe2\x82\xac</td>
        </tr>
        </tbody>
        </table>
        </body>
        </html>'''
        self.encoding = 'utf-8'

def test_accounts_page_successfully_iter_through_accounts():
    data = {
        'account_1': {
            'id': 'N0001',
            'label': 'Account (N0001)',
            'balance': 42.00,
            'currency': 'EUR',
        },
        'account_2': {
            'id': 'N0002',
            'label': 'Account (N0002)',
            'balance': 4242.00,
            'currency': 'EUR',
        },
    }

    response = MockResponseAccount()
    page = AccountsPage(FakeoneBrowser('login', 'password'), response)
    accounts = list(page.iter_accounts())

    for account, data in zip(accounts, data.values()):

        assert account.id == data['id']
        assert account.label == data['label']
        assert account.balance == data['balance']
        assert account.currency == data['currency']



class MockResponseHistory:
    
    def __init__(self, *args, **kwargs):
        self.url = 'http://random-url.com'
        self.content = b'''<html>
        <body>
        <table>
        <tbody>
            <tr>
                <td>28/01/2021</td>
                <td>VIREMENT SALAIRE</td>
                <td>+4 242,00</td>
                <td></td>
            </tr>
            <tr>
                <td>29/01/2021</td>
                <td>PAIEMENT CB RESTAURANT 19000101</td>
                <td></td>
                <td>-30,00</td>
            </tr>
            <tr>
                <td>29/01/2021</td>
                <td>PAIEMENT CB CINEMA 20420101</td>
                <td></td>
                <td>-10,00</td>
            </tr>
        </tbody>
        </table>
        </body>
        </html>'''
        self.encoding = 'utf-8'

def test_history_page_successfully_iter_through_history_account():

    data = {
        'operation_1': {
            'date': '28/01/2021',
            'label': 'VIREMENT SALAIRE',
            'amount': 4242.00,
        },
        'operation_2': {
            'date': '29/01/2021',
            'label': 'PAIEMENT CB RESTAURANT 19000101',
            'amount': -30.00,
        },
        'operation_3': {
            'date': '29/01/2021',
            'label': 'PAIEMENT CB CINEMA 20420101',
            'amount': -10.00,
        },
    }

    response_account = MockResponseAccount()
    accounts_page = AccountsPage(FakeoneBrowser('login', 'password'), response_account)
    accounts = list(accounts_page.iter_accounts())

    response_history = MockResponseHistory()
    history_page = HistoryAccount(FakeoneBrowser('login', 'password'), response_history)
    history_account = list(history_page.iter_history(accounts[0]))

    for history, data in zip(history_account, data.values()):

        assert history.date.strftime('%d/%m/%Y') == data['date']
        assert history.label == data['label']
        assert history.amount == data['amount']
