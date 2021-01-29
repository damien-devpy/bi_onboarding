from modules.fakeone.browser import FakeoneBrowser
from modules.fakeone.pages import AccountsPage

class MockResponse:

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

    response = MockResponse()
    page = AccountsPage(FakeoneBrowser('login', 'password'), response)

    accounts = list(page.iter_accounts())

    for account, data in zip(accounts, data.values()):

        assert account.id == data['id']
        assert account.label == data['label']
        assert account.balance == data['balance']
        assert account.currency == data['currency']