# -*- mode: python; python-indent: 4 -*-
"""Docstring Missing."""

import ipaddress

from .network import Network
from itertools import product
from ncs.maagic import ListElement,PresenceContainer
from ncs.template import Template,Variables


class L3vpn(Network):
    """Docstring Missing."""

    def __setup_vrf(self, device: ListElement, base_vars: list[str]) -> None:
        """Configure VRF routing instances

        Args:
            device (ListElement): Network device
            base_vars (list[str]): Base variables
        """        
        self.log.info('CONFIGURING VRF')
        template = Template(self.service)
        vars = Variables(base_vars)
        vars.add('REDISTRIBUTION-PROTOCOL', '')
        if device.redistribute:
            for protocol in device.redistribute:
                vars.add('REDISTRIBUTION-PROTOCOL', str(protocol))
                template.apply('l3vpn-vrf', vars)
        else:
            template.apply('l3vpn-vrf', vars)

    def __setup_intf(self, device: ListElement, intf: ListElement, base_vars: list[str]) -> None:
        """Configure network device interfaces. Validates that interfaces are compliant
        with existing resources allocated for existing interfaces on the network device

        Args:
            device (ListElement): Network device
            intf (ListElement): Interface list
            base_vars (list[str]): Base variables
        """        
        self.log.info('CONFIGURING INTERFACE: ', intf.name)
        template = Template(self.service)
        vars = Variables(base_vars)
        intf_type, intf_id = self.get_intf_type_and_id(device.name, intf.name)
        self.validate_interface(device.name, intf, intf_type, intf_id)
        vars.add('INTERFACE-NAME', intf.name)
        vars.add('INTERFACE-TYPE', intf_type)
        vars.add('INTERFACE-ID', intf_id)
        vars.add('MTU', intf.mtu)
        vars.add('PORT-MODE', intf.port_mode)
        vars.add('ENCAPSULATION', '')
        vars.add('VLAN-ID', '')
        vars.add('INNER-VLAN-ID', '')
        vars.add('IPV4-LOCAL-ADDRESS', '')
        vars.add('IPV4-LOCAL-MASK', '')
        vars.add('IPV6-LOCAL-PREFIX', '')
        if intf.ipv4_local_prefix:
            ip_address, ip_mask = self.get_ip_and_mask(intf.ipv4_local_prefix)
            vars.add('IPV4-LOCAL-ADDRESS', ip_address)
            vars.add('IPV4-LOCAL-MASK', ip_mask)

        if intf.ipv6_local_prefix:
            vars.add('IPV6-LOCAL-PREFIX', intf.ipv6_local_prefix)
        
        template.apply('l3vpn-intf', vars)

        if not intf.port_mode:
            for vlan_id in intf.vlan_id.as_list():
                vars.add('VLAN-ID', vlan_id)
                template.apply('l3vpn-intf', vars)

            if intf.inner_vlan_id:
                for inner_vlan_id in intf.inner_vlan_id.as_list():
                    vars.add('INNER-VLAN-ID', inner_vlan_id)
                    template.apply('l3vpn-intf', vars)

    def __setup_policy(self, intf: str, base_vars: list[str]) -> None:
        """Configure policy

        Args:
            intf (str): Network device interface
            base_vars (list[str]): Base variables
        """        
        self.log.info('CONFIGURING POLICY FOR INTERFACE: ', intf.name)
        template_policy = Template(self.service)
        policy_vars = Variables(base_vars)
        policy_vars.add('CIR', intf.cir)
        template_policy.apply('l3vpn-policy', policy_vars)

    def __setup_static_routing(self, device: ListElement, static: PresenceContainer, base_vars: list[str]) -> None:
        """Configure CE static routing. For each static route, loop through all forwarding addresses, and subsequently through
        each interface on the device to ensure that each forwarding address falls within at least one of the IPv4 networks 
        configured on the device interfaces

        Args:
            device (ListElement): Network device
            static (PresenceContainer): Static routing container
            base_vars (list[str]): Base variables
        """        
        self.log.info('CONFIGURING STATIC ROUTES')
        template_static = Template(self.service)
        static_vars = Variables(base_vars)
        static_vars.add('IPV4-DEST-PREFIX', '')
        static_vars.add('IPV4-FORWARDING', '')
        static_vars.add('IPV6-DEST-PREFIX', '')
        static_vars.add('IPV6-FORWARDING', '')

        # IPv4
        for prefix, intf in product(static.ipv4_destination_prefix, device.interface):
            static_vars.add('IPV4-DEST-PREFIX', prefix.ipv4_prefix)
            for forwarding_address in prefix.ipv4_forwarding.as_list():
                if intf.ipv4_local_prefix:
                    intf_network = ipaddress.ip_interface(intf.ipv4_local_prefix).network

                    if self.check_ip_host_in_network(forwarding_address, intf_network):
                        static_vars.add('IPV4-FORWARDING', forwarding_address)
                        template_static.apply('l3vpn-static', static_vars)
                    
                    # TODO: Exception needs to take into account having more than one interface per device as well as more than forwarding address per static route
                    # else:
                    #     raise Exception(f'The ipv4-forwarding address {forwarding_address} for ipv4-destination-prefix {prefix.ipv4_prefix} on {device.name} does not fall within {intf_network}')


        # IPv6
        for prefix in static.ipv6_destination_prefix:
            static_vars.add('IPV6-DEST-PREFIX', prefix.ipv6_prefix)

            for forwarding_address in prefix.ipv6_forwarding.as_list():
                for intf in device.interface:
                    if intf.ipv6_local_prefix:
                        intf_network = ipaddress.ip_interface(intf.ipv6_local_prefix).network

                        if self.check_ip_host_in_network(forwarding_address, intf_network):
                            static_vars.add('IPV6-FORWARDING', forwarding_address)
                            template_static.apply('l3vpn-static', static_vars)
                        
                        # TODO: Exception needs to take into account having more than one interface per device as well as more than forwarding address per static route
                        # else:
                        #     raise Exception(f'The ipv4-forwarding address {forwarding_address} for ipv4-destination-prefix {prefix.ipv4_prefix} on {device.name} does not fall within {intf_network}')

    def __setup_bgp_routing(self, device: ListElement, bgp: PresenceContainer, base_vars: list[str]) -> None:
        """Configure BGP CE Routing

        Args:
            device (ListElement): Network device
            bgp (PresenceContainer): BGP routing container
            base_vars (list[str]): Base variables
        """        
        self.log.info('CONFIGURING BGP')
        template_bgp = Template(self.service)
        bgp_vars = Variables(base_vars)
        bgp_vars.add('IPv4-BGP-NEIGHBOR', '')
        bgp_vars.add('IPv6-BGP-NEIGHBOR', '')
        bgp_vars.add('BGP-NEIGHBOR-PASSWORD', '')
        bgp_vars.add("BGP-NEIGHBOR-ASN", bgp.asn)
        bgp_vars.add("BGP-ROUTE-POLICY-IN", bgp.route_policy_in)
        bgp_vars.add("BGP-ROUTE-POLICY-OUT", bgp.route_policy_out)

        for bgp_neighbor in bgp.ipv4_neighbor:
            bgp_vars.add('IPv4-BGP-NEIGHBOR', bgp_neighbor.address)
            bgp_vars.add('BGP-NEIGHBOR-PASSWORD', bgp_neighbor.password)
            template_bgp.apply('l3vpn-bgp', bgp_vars)

        for bgp_neighbor in bgp.ipv6_neighbor:
            bgp_vars.add('IPv6-BGP-NEIGHBOR', bgp_neighbor.address)
            bgp_vars.add('BGP-NEIGHBOR-PASSWORD', bgp_neighbor.password)
            template_bgp.apply('l3vpn-bgp', bgp_vars)

    def configure(self) -> None:
        """Docstring missing."""
        base_vars = []
        base_vars.append(('CUSTOMER-NAME', customer_name := self.service.customer_name))
        base_vars.append(('SERVICE-ID', service_id := self.service.service_id))
        base_vars.append(('VPN-ID', vpn_id := self.service.vpn_id))
        base_vars.append(('INET', inet := self.service.inet))
        base_vars.append(('MAX-ROUTES', max_routes := self.service.max_routes))
        base_vars.append(('MAX-ROUTES-WARNING', max_routes_warning := self.service.max_routes_warning))
        base_vars.append(('AS-NUMBER', pe_asn := self.service.provider_edge.asn))

        for device in self.service.provider_edge.device:
            self.log.info('CONFIGURING DEVICE: ', device_name := device.name)
            base_vars.append(('RD', rd := f'{self.get_loopback_ip(device.name, 0)}:{self.service.vpn_id}'))
            base_vars.append(('DEVICE-NAME', device_name))

            self.log.info('ASSIGNING VRF NAME: ', vrf_name := self.get_vrf_name(device_name, service_id, vpn_id))
            base_vars.append(('VRF', vrf_name))

            self.__setup_vrf(device, base_vars)

            for intf in device.interface:
                self.__setup_intf(device, intf, base_vars)
                self.__setup_policy(intf, base_vars)

            if device.ce_routing.static:
                self.__setup_static_routing(device, device.ce_routing.static, base_vars)

            if device.ce_routing.bgp:
                self.__setup_bgp_routing(device, device.ce_routing.bgp, base_vars)
