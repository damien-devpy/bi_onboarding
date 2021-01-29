from weboob.core import Weboob

def test_that_backend_load_successfully():
    w = Weboob()
    loaded = w.load_backends(modules="fakeone")
    assert "{'fakeone': <Backend 'fakeone'>}" in str(loaded)
