import ncs


def test_service_lifecycle(maapi):
    # CREATE
    with maapi.start_write_trans() as t:
        root = ncs.maagic.get_root(t)
        svc = root.services.l3vpn.create('pytest-customer', 'pytest-l3vpn-01')
        svc.vpn_id = 999
        svc.inet = 'IPv4'
        svc.provider_edge.asn = 65000

        pe0 = svc.provider_edge.device.create('iosxr-0')
        pe0.redistribute.create('connected')
        iface0 = pe0.interface.create('GigabitEthernet2/0')
        iface0.port_mode = True
        iface0.ipv4_local_prefix = '10.100.10.1/29'

        pe1 = svc.provider_edge.device.create('iosxr-1')
        pe1.redistribute.create('connected')
        iface1 = pe1.interface.create('GigabitEthernet2/0')
        iface1.port_mode = True
        iface1.ipv4_local_prefix = '10.100.10.9/29'

        t.apply()

    try:
        # READ
        with maapi.start_read_trans() as t:
            root = ncs.maagic.get_root(t)
            assert ('pytest-customer', 'pytest-l3vpn-01') in root.services.l3vpn
            svc = root.services.l3vpn['pytest-customer', 'pytest-l3vpn-01']
            assert svc.vpn_id == 999
            assert str(svc.inet) == 'IPv4'
    finally:
        # DELETE
        with maapi.start_write_trans() as t:
            root = ncs.maagic.get_root(t)
            if ('pytest-customer', 'pytest-l3vpn-01') in root.services.l3vpn:
                del root.services.l3vpn['pytest-customer', 'pytest-l3vpn-01']
                t.apply()

    # VERIFY DELETE
    with maapi.start_read_trans() as t:
        root = ncs.maagic.get_root(t)
        assert ('pytest-customer', 'pytest-l3vpn-01') not in root.services.l3vpn
