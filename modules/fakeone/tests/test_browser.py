from fakeone.browser import FakeoneBrowser
from weboob.exceptions import BrowserIncorrectPassword
import pytest

def test_browser_detect_unsuccessful_connexion_from_invalid_credentials():
    browser = FakeoneBrowser('foo', 'wrong_password')

    with pytest.raises(BrowserIncorrectPassword) as err:
        browser.do_login()

def test_browser_successfully_login_with_valid_credentials():
    browser = FakeoneBrowser('foo', 'bar')
    browser.do_login()

    assert bool(browser.session.cookies.values()) is True