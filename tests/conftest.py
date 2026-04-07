import pytest
import ncs


@pytest.fixture(scope='session')
def maapi():
    with ncs.maapi.Maapi() as m:
        with ncs.maapi.Session(m, 'admin', 'python'):
            yield m


@pytest.fixture(scope='session', autouse=True)
def test_customer(maapi):
    """Create a test customer to satisfy the customer-name leafref; tear it down after the session."""
    with maapi.start_write_trans() as t:
        root = ncs.maagic.get_root(t)
        if 'pytest-customer' not in root.customers.customer:
            root.customers.customer.create('pytest-customer')
            t.apply()
    # yield pauses setup here; pytest runs all tests, then resumes below for teardown
    yield
    with maapi.start_write_trans() as t:
        root = ncs.maagic.get_root(t)
        if 'pytest-customer' in root.customers.customer:
            del root.customers.customer['pytest-customer']
            t.apply()
