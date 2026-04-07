# NSO Package Testing Framework

Tests are written in [pytest](https://pytest.org) and interact with a live NSO instance directly via MAAPI (NSO Python API).

## Prerequisites

- NSO running with the `l3vpn` package loaded
- NETSIM devices available in NSO
- NSO environment sourced before running tests:

```bash
source ~/nso/<version>/ncsrc
```

## Makefile Integration

Testing is initiated with:

```bash
make test
```

The `test-packages` target creates an isolated Python virtual environment, installs dependencies from `tests/requirements.txt`, runs pytest, then tears the environment down. The venv is not persisted between runs.

## How It Works

Fixtures are defined in `conftest.py` and are automatically discovered by pytest. Two session-scoped fixtures manage shared state across all tests:

- **`maapi`** — opens a single MAAPI connection and user session for the duration of the test run; injected into any test or fixture that declares it as a parameter
- **`test_customer`** — creates the `pytest-customer` NSO customer required by the `customer-name` leafref before any tests run; tears it down after the session. Runs automatically via `autouse=True`

Tests are defined in `test_service.py`. Each test function that declares `maapi` as a parameter receives the shared session object and is responsible for its own service lifecycle (create, assert, delete).

## Included Test Cases

| Test | Description |
|------|-------------|
| `test_service_lifecycle` | IPv4, two PE devices, port-mode true, no CE routing |

## Adding a Test Case

1. Use the NSO CLI to configure the desired service instance
2. Translate the configuration into a `test_*` function in `test_service.py` using MAAPI
3. Follow the CREATE → READ → DELETE pattern with a `try/finally` block to ensure cleanup on assertion failure

### Pattern

```python
def test_service_lifecycle(maapi):
    # CREATE
    with maapi.start_write_trans() as t:
        root = ncs.maagic.get_root(t)
        svc = root.services.l3vpn.create('<customer>', '<service-id>')
        # ... set service parameters ...
        t.apply()

    try:
        # READ
        with maapi.start_read_trans() as t:
            root = ncs.maagic.get_root(t)
            assert ('<customer>', '<service-id>') in root.services.l3vpn
            # ... assert service parameters ...
    finally:
        # DELETE
        with maapi.start_write_trans() as t:
            root = ncs.maagic.get_root(t)
            if ('<customer>', '<service-id>') in root.services.l3vpn:
                del root.services.l3vpn['<customer>', '<service-id>']
                t.apply()

    # VERIFY DELETE
    with maapi.start_read_trans() as t:
        root = ncs.maagic.get_root(t)
        assert ('<customer>', '<service-id>') not in root.services.l3vpn
```

The `try/finally` ensures DELETE always runs even if a READ assertion fails, keeping NSO clean between test runs.

## NETSIM Setup

Update the device names in `test_service.py` to match your NETSIM environment before running.
