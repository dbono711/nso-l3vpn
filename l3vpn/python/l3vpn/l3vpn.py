# -*- mode: python; python-indent: 4 -*-
import ncs
import re

from l3vpn.utils import Device
from l3vpn.utils import Network


class L3vpn(Device, Network):
    """Docstring Missing."""
    def __init__(self, log, root, service):
        """Docstring Missing."""
        Device.__init__(self, log, root, service)
        Network.__init__(self, log, root, service)

    def setup_vrf(self, device, base_vars=[]):
        """Docstring Missing."""
        self.log.info("Configuring VRF's")
        template_vrf = ncs.template.Template(self.service)
        vrf_vars = ncs.template.Variables(base_vars)

        # Derive Route Distinguisher (RD) from combination of the PE
        # Loopback0 IP and the Service ID
        rd = f"1:{self.get_loopback0_ip(device.device_name)}:{self.service.vpn_id}"
        vrf_vars.add("RD", rd)

        for protocol in device.redistribution:
            vrf_vars.add("REDISTRIBUTION-PROTOCOL", str(protocol))
            template_vrf.apply('l3vpn-vrf', vrf_vars)

    def setup_policy(self, intf, base_vars=[]):
        """Docstring Missing."""
        self.log.info("Configuring policies")
        template_policy = ncs.template.Template(self.service)
        policy_vars = ncs.template.Variables(base_vars)
        policy_vars.add("CIR", intf.cir)
        template_policy.apply('l3vpn-policy', policy_vars)

    def setup_intf(self, intf, base_vars=[]):
        """Docstring Missing."""
        self.log.info("Configuring interfaces")
        template_intf = ncs.template.Template(self.service)
        intf_vars = ncs.template.Variables(base_vars)
        intf_type, intf_id = re.split(r'(^.*\B)', intf.name)[1:]
        intf_vars.add("INTERFACE-TYPE", intf_type)
        intf_vars.add("INTERFACE-ID", intf_id)
        intf_vars.add("MTU", intf.mtu)
        intf_vars.add("PORT-MODE", intf.port_mode)

        # if (str(self.service.inet) == 'IPv4' or str(self.service.inet) == 'IPv4-IPv6') and intf.ipv4_local_prefix is not None:
        #     (ipv4_address, ipv4_mask) = self.get_ipv4_ip_and_netmask(intf.ipv4_local_prefix)
        #     template_vars_l3vpn.add("IPV4-LOCAL-ADDRESS", ipv4_address)
        #     template_vars_l3vpn.add("IPV4-LOCAL-MASK", ipv4_mask)
        #
        # if (str(self.service.inet) == 'IPv6' or str(self.service.inet) == 'IPv4-IPv6') and intf.ipv6_local_prefix is not None:
        #     template_vars_l3vpn.add("IPV6-LOCAL-PREFIX", intf.ipv6_local_prefix)

        # if not intf.port_mode:
        #     template_vars_l3vpn.add("ENCAPSULATION", intf.encapsulation)
        #
        #     for vlan_id in intf.vlan_id.as_list():
        #         template_vars_l3vpn.add("VLAN-ID", vlan_id)
        #         common_template_l3vpn.apply('l3vpn-iosxr-template', template_vars_l3vpn)
        #
        #     if intf.inner_vlan_id:
        #         for inner_vlan_id in intf.inner_vlan_id.as_list():
        #             template_vars_l3vpn.add("INNER-VLAN-ID", inner_vlan_id)
        #             common_template_l3vpn.apply('l3vpn-iosxr-template', template_vars_l3vpn)

        template_policy.apply('l3vpn-intf', intf_vars)

    def configure(self):
        """Docstring Missing."""
        base_vars = []
        base_vars.append(("CUSTOMER-NAME", self.service.customer_name))
        base_vars.append(("SERVICE-ID", self.service.service_id))
        base_vars.append(("VPN-ID", self.service.vpn_id))
        base_vars.append(("AS-NUMBER", self.service.as_number))
        base_vars.append(("INET", self.service.inet))
        base_vars.append(("MAX-ROUTES", self.service.max_routes))
        base_vars.append(("MAX-ROUTES-WARNING", self.service.max_routes_warning))

        # Derive VRF name from combination of Service ID and VPN ID,
        # accomodate Cisco IOS-XR character/length limitations for VRF Name
        service_id = re.sub(r'[\.\(\)\, ]', '_', self.service.service_id)[:32]
        vrf = f"{service_id}:{str(self.service.vpn_id)}"
        base_vars.append(("VRF", vrf))

        for device in self.service.device:
            self.log.info(f"@ Configuring device: {device.device_name} @")
            base_vars.append(("DEVICE-NAME", device.device_name))
            self.setup_vrf(device, base_vars)

            for intf in device.interface:
                self.setup_intf(intf, base_vars)
                self.setup_policy(intf, base_vars)

        #     common_template_l3vpn = ncs.template.Template(self.service)
        #     template_vars_l3vpn.add("DEVICE-NAME", device.device_name)
        #     template_vars_l3vpn.add("STATIC-ENABLED", 'FALSE')
        #     template_vars_l3vpn.add("BGP-ENABLED", 'FALSE')
        #     template_vars_l3vpn.add("INTERFACE-TYPE", '')
        #     template_vars_l3vpn.add("INTERFACE-ID", '')
        #     template_vars_l3vpn.add("IPV4-LOCAL-ADDRESS", '')
        #     template_vars_l3vpn.add("IPV4-LOCAL-MASK", '')
        #     template_vars_l3vpn.add("IPV6-LOCAL-PREFIX", '')
        #     template_vars_l3vpn.add("ENCAPSULATION", '')
        #     template_vars_l3vpn.add("VLAN-ID", '')
        #     template_vars_l3vpn.add("INNER-VLAN-ID", '')
        #     template_vars_l3vpn.add("IPV4-STATIC-DEST-PREFIX", '')
        #     template_vars_l3vpn.add("IPV4-STATIC-FORWARDING", '')
        #     template_vars_l3vpn.add("IPV6-STATIC-DEST-PREFIX", '')
        #     template_vars_l3vpn.add("IPV6-STATIC-FORWARDING", '')
        #     template_vars_l3vpn.add("BGP-NEIGHBOR-ASN", '')
        #     template_vars_l3vpn.add("BGP-ROUTE-POLICY-IN", '')
        #     template_vars_l3vpn.add("BGP-ROUTE-POLICY-OUT", '')
        #     template_vars_l3vpn.add("BGP-NEIGHBOR-PASSWORD", '')
        #     template_vars_l3vpn.add("IPv4-BGP-NEIGHBOR", '')
        #     template_vars_l3vpn.add("IPv6-BGP-NEIGHBOR", '')
        #     template_vars_l3vpn.add("REDISTRIBUTION-PROTOCOL", '')

            # for intf in device.interface:
            #     template_vars_l3vpn.add("CIR", intf.cir)

            # interfaces
            # if device.interface:
            #     self.log.info("Configuring interfaces")
            #     self.check_interface_config_allowed(device)
            #
            #     for intf in device.interface.GigabitEthernet_iosxr:
            #         template_vars_l3vpn.add("IPV4-LOCAL-ADDRESS", '')
            #         template_vars_l3vpn.add("IPV4-LOCAL-MASK", '')
            #         template_vars_l3vpn.add("IPV6-LOCAL-PREFIX", '')
            #         template_vars_l3vpn.add("ENCAPSULATION", '')
            #         template_vars_l3vpn.add("VLAN-ID", '')
            #         template_vars_l3vpn.add("INNER-VLAN-ID", '')
            #         template_vars_l3vpn.add("INTERFACE-TYPE", 'GigabitEthernet')
            #         template_vars_l3vpn.add("INTERFACE-ID", intf.interface_id)
            #
            #         if (str(self.service.inet) == 'IPv4' or str(self.service.inet) == 'IPv4-IPv6') and intf.ipv4_local_prefix is not None:
            #             (ipv4_address, ipv4_mask) = self.get_ipv4_ip_and_netmask(intf.ipv4_local_prefix)
            #             template_vars_l3vpn.add("IPV4-LOCAL-ADDRESS", ipv4_address)
            #             template_vars_l3vpn.add("IPV4-LOCAL-MASK", ipv4_mask)
            #
            #         if (str(self.service.inet) == 'IPv6' or str(self.service.inet) == 'IPv4-IPv6') and intf.ipv6_local_prefix is not None:
            #             template_vars_l3vpn.add("IPV6-LOCAL-PREFIX", intf.ipv6_local_prefix)
            #
            #         if not intf.port_mode:
            #             template_vars_l3vpn.add("ENCAPSULATION", intf.encapsulation)
            #
            #             for vlan_id in intf.vlan_id.as_list():
            #                 template_vars_l3vpn.add("VLAN-ID", vlan_id)
            #                 common_template_l3vpn.apply('l3vpn-iosxr-template', template_vars_l3vpn)
            #
            #             if intf.inner_vlan_id:
            #                 for inner_vlan_id in intf.inner_vlan_id.as_list():
            #                     template_vars_l3vpn.add("INNER-VLAN-ID", inner_vlan_id)
            #                     common_template_l3vpn.apply('l3vpn-iosxr-template', template_vars_l3vpn)
            #
            #         common_template_l3vpn.apply('l3vpn-iosxr-template', template_vars_l3vpn)

            # static routes
            # static = device.static
            # if static:
            #     self.log.info("Configuring static routes")
            #     template_vars_l3vpn.add("STATIC-ENABLED", 'TRUE')
            #     for ipv4_static_destination_prefix in static.ipv4_static_destination_prefix:
            #         template_vars_l3vpn.add("IPV4-STATIC-DEST-PREFIX", ipv4_static_destination_prefix.ipv4_prefix)
            #
            #         for forwarding in ipv4_static_destination_prefix.ipv4_static_forwarding:
            #             template_vars_l3vpn.add("IPV4-STATIC-FORWARDING", forwarding)
            #             common_template_l3vpn.apply('l3vpn-iosxr-template', template_vars_l3vpn)
            #
            #         common_template_l3vpn.apply('l3vpn-iosxr-template', template_vars_l3vpn)
            #
            #     for ipv6_static_destination_prefix in static.ipv6_static_destination_prefix:
            #         template_vars_l3vpn.add("IPV6-STATIC-DEST-PREFIX", ipv6_static_destination_prefix.ipv6_prefix)
            #         template_vars_l3vpn.add("IPV6-STATIC-FORWARDING", ipv6_static_destination_prefix.ipv6_static_forwarding)
            #         common_template_l3vpn.apply('l3vpn-iosxr-template', template_vars_l3vpn)

            # bgp
            # bgp = device.bgp
            # if bgp:
            #     self.log.info("Configuring bgp")
            #     template_vars_l3vpn.add("BGP-ENABLED", 'TRUE')
            #     template_vars_l3vpn.add("BGP-NEIGHBOR-ASN", bgp.bgp_neighbor_asn)
            #     template_vars_l3vpn.add("BGP-ROUTE-POLICY-IN", bgp.bgp_route_policy_in)
            #     template_vars_l3vpn.add("BGP-ROUTE-POLICY-OUT", bgp.bgp_route_policy_out)
            #     for bgp_neighbor in bgp.ipv4_bgp_neighbor:
            #         template_vars_l3vpn.add("IPv4-BGP-NEIGHBOR", bgp_neighbor.bgp_neighbor_address)
            #         template_vars_l3vpn.add("BGP-NEIGHBOR-PASSWORD", bgp_neighbor.bgp_neighbor_password or '')
            #         common_template_l3vpn.apply('l3vpn-iosxr-template', template_vars_l3vpn)
            #
            #     for bgp_neighbor in bgp.ipv6_bgp_neighbor:
            #         template_vars_l3vpn.add("IPv6-BGP-NEIGHBOR", bgp_neighbor.bgp_neighbor_address)
            #         template_vars_l3vpn.add("BGP-NEIGHBOR-PASSWORD", bgp_neighbor.bgp_neighbor_password or '')
            #         common_template_l3vpn.apply('l3vpn-iosxr-template', template_vars_l3vpn)

            # common_template_l3vpn.apply('l3vpn-template', template_vars_l3vpn)
