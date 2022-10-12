# -*- mode: python; python-indent: 4 -*-
"""Docstring Missing."""

import ipaddress
import ncs
import re

from l3vpn.network import Network


class L3vpn(Network):
    """Docstring Missing."""

    def __setup_vrf(self, device, base_vars=[]):
        """Docstring Missing."""
        self.log.info('Configuring vrf')
        template_vrf = ncs.template.Template(self.service)
        vrf_vars = ncs.template.Variables(base_vars)
        rd = f'{self.get_loopback_ip(device.name, 0)}:{self.service.vpn_id}' # Route Distinguisher = Loopback0 IP:VPN ID
        vrf_vars.add('RD', rd)
        vrf_vars.add('REDISTRIBUTION-PROTOCOL', '')
        if device.redistribute:
            for protocol in device.redistribute:
                vrf_vars.add('REDISTRIBUTION-PROTOCOL', str(protocol))
                template_vrf.apply('l3vpn-vrf', vrf_vars)
        else:
            template_vrf.apply('l3vpn-vrf', vrf_vars)

    def __setup_intf(self, device, intf, base_vars=[]):
        """Docstring Missing."""
        template_intf = ncs.template.Template(self.service)
        intf_vars = ncs.template.Variables(base_vars)
        intf_type, intf_id = self.get_intf_type_and_id(intf.name)
        self.validate_interface(device.name, intf, intf_type, intf_id)
        intf_vars.add('INTERFACE-NAME', intf.name)
        intf_vars.add('INTERFACE-TYPE', intf_type)
        intf_vars.add('INTERFACE-ID', intf_id)
        intf_vars.add('MTU', intf.mtu)
        intf_vars.add('PORT-MODE', intf.port_mode)
        intf_vars.add('ENCAPSULATION', '')
        intf_vars.add('VLAN-ID', '')
        intf_vars.add('INNER-VLAN-ID', '')
        intf_vars.add('IPV4-LOCAL-ADDRESS', '')
        intf_vars.add('IPV4-LOCAL-MASK', '')
        intf_vars.add('IPV6-LOCAL-PREFIX', '')
        if intf.ipv4_local_prefix is not None:
            ip_address, ip_mask = self.get_ip_and_mask(intf.ipv4_local_prefix)
            intf_vars.add('IPV4-LOCAL-ADDRESS', ip_address)
            intf_vars.add('IPV4-LOCAL-MASK', ip_mask)

        if intf.ipv6_local_prefix is not None:
            intf_vars.add('IPV6-LOCAL-PREFIX', intf.ipv6_local_prefix)

        if not intf.port_mode:
            for vlan_id in intf.vlan_id.as_list():
                intf_vars.add('VLAN-ID', vlan_id)
                template_intf.apply('l3vpn-intf', intf_vars)

            if intf.inner_vlan_id:
                for inner_vlan_id in intf.inner_vlan_id.as_list():
                    intf_vars.add('INNER-VLAN-ID', inner_vlan_id)
                    template_intf.apply('l3vpn-intf', intf_vars)

        template_intf.apply('l3vpn-intf', intf_vars)

    def __setup_policy(self, intf, base_vars=[]):
        """Docstring Missing."""
        template_policy = ncs.template.Template(self.service)
        policy_vars = ncs.template.Variables(base_vars)
        policy_vars.add('CIR', intf.cir)
        template_policy.apply('l3vpn-policy', policy_vars)

    def __setup_static_routing(self, device, static, base_vars=[]):
        """Docstring Missing."""
        self.log.info('Configuring static routes')
        template_static = ncs.template.Template(self.service)
        static_vars = ncs.template.Variables(base_vars)
        static_vars.add('IPV4-DEST-PREFIX', '')
        static_vars.add('IPV4-FORWARDING', '')
        static_vars.add('IPV6-DEST-PREFIX', '')
        static_vars.add('IPV6-FORWARDING', '')

        for ipv4_destination_prefix in static.ipv4_destination_prefix:
            static_vars.add('IPV4-DEST-PREFIX', ipv4_destination_prefix.ipv4_prefix)

            for intf in device.interface:
                for forwarding in ipv4_destination_prefix.ipv4_forwarding.as_list():
                    intf_network = ipaddress.ip_interface(intf.ipv4_local_prefix).network
                    if not self.check_ip_host_in_network(forwarding, intf_network):
                        raise Exception(f'Forwarding hop "{forwarding}" for static route "{ipv4_destination_prefix.ipv4_prefix}" does not fall within the "{intf_network}" prefix on "{intf.name}"')
                    static_vars.add('IPV4-FORWARDING', forwarding)
                    template_static.apply('l3vpn-static', static_vars)

        for ipv6_destination_prefix in static.ipv6_destination_prefix:
            static_vars.add('IPV6-DEST-PREFIX', ipv6_destination_prefix.ipv6_prefix)

            for intf in device.interface:
                intf_network = ipaddress.ip_interface(intf.ipv6_local_prefix).network
                if not self.check_ip_host_in_network(ipv6_destination_prefix.ipv6_forwarding, intf_network):
                    raise Exception(f'Forwarding hop "{ipv6_destination_prefix.ipv6_forwarding}" for static route "{ipv6_destination_prefix.ipv6_prefix}" does not fall within the "{intf_network}" prefix on "{intf.name}"')
                static_vars.add('IPV6-FORWARDING', ipv6_destination_prefix.ipv6_forwarding)
                template_static.apply('l3vpn-static', static_vars)

    def __setup_bgp_routing(self, device, bgp, base_vars=[]):
        """Docstring Missing."""
        self.log.info("Configuring BGP")
        template_bgp = ncs.template.Template(self.service)
        bgp_vars = ncs.template.Variables(base_vars)
        bgp_vars.add("BGP-NEIGHBOR-ASN", bgp.asn)
        bgp_vars.add("BGP-ROUTE-POLICY-IN", bgp.route_policy_in)
        bgp_vars.add("BGP-ROUTE-POLICY-OUT", bgp.route_policy_out)

        for bgp_neighbor in bgp.ipv4_bgp_neighbor:
            bgp_vars.add("IPv4-BGP-NEIGHBOR",
                         bgp_neighbor.bgp_neighbor_address)
            bgp_vars.add("BGP-NEIGHBOR-PASSWORD",
                         bgp_neighbor.bgp_neighbor_password or '')
            template_bgp.apply('l3vpn-bgp', bgp_vars)

        for bgp_neighbor in bgp.ipv6_bgp_neighbor:
            bgp_vars.add("IPv6-BGP-NEIGHBOR",
                         bgp_neighbor.bgp_neighbor_address)
            bgp_vars.add("BGP-NEIGHBOR-PASSWORD",
                         bgp_neighbor.bgp_neighbor_password or '')
            template_bgp.apply('l3vpn-bgp', bgp_vars)

        template_bgp.apply('l3vpn-bgp', bgp_vars)

    def configure(self):
        """Docstring Missing."""
        base_vars = []
        base_vars.append(('CUSTOMER-NAME', self.service.customer_name))
        base_vars.append(('SERVICE-ID', self.service.service_id))
        base_vars.append(('VPN-ID', self.service.vpn_id))
        base_vars.append(('INET', self.service.inet))
        base_vars.append(('MAX-ROUTES', self.service.max_routes))
        base_vars.append(('MAX-ROUTES-WARNING', self.service.max_routes_warning))
        base_vars.append(('AS-NUMBER', self.service.provider_edge.asn))

        # Derive VRF name from a combination of Service ID and VPN ID,
        # accomodates for Cisco IOS-XR character/length limitations
        vrf_service_id = re.sub(r'[\.\(\)\, ]', '_', self.service.service_id)[:32]
        vrf = f'{vrf_service_id}:{str(self.service.vpn_id)}'
        base_vars.append(('VRF', vrf))

        for device in self.service.provider_edge.device:
            self.log.info(f'Configuring device: {device.name}')
            base_vars.append(('DEVICE-NAME', device.name))
            self.__setup_vrf(device, base_vars)

            for intf in device.interface:
                self.log.info(f'Configuring interface {intf.name}')
                self.__setup_intf(device, intf, base_vars)
                self.log.info(f'Configuring policy for interface {intf.name}')
                self.__setup_policy(intf, base_vars)

            if device.ce_routing.static:
                self.__setup_static_routing(device, device.ce_routing.static, base_vars)

            # if device.ce_routing.bgp:
            #     self.__setup_bgp_routing(
            #         device, device.ce_routing.bgp, base_vars)
