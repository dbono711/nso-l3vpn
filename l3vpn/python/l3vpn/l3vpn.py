# -*- mode: python; python-indent: 4 -*-
"""Docstring Missing."""


import ipaddress
from itertools import product

from ncs.maagic import ListElement, PresenceContainer
from ncs.template import Template, Variables
from resource_manager.service.allocator import Allocator

from .context import ServiceContext
from .device import Device
from .network import Network


class L3vpn:
    """Docstring Missing."""

    def __init__(self, ctx: ServiceContext) -> None:
        self.ctx = ctx
        self.network = Network(ctx)
        self.device = Device(ctx)

    def _setup_vrf(self, device: ListElement, base_vars: list[str]) -> None:
        """Configure VRF routing instances

        Args:
            device (ListElement): Network device
            base_vars (list[str]): Base variables
        """
        self.ctx.log.info("Configuring VRF")
        template = Template(self.ctx.service)
        vrf_vars = Variables(base_vars)
        vrf_vars.add("REDISTRIBUTION-PROTOCOL", "")

        template.apply("l3vpn-vrf", vrf_vars)

        for protocol in device.redistribute:
            vrf_vars.add("REDISTRIBUTION-PROTOCOL", str(protocol))
            template.apply("l3vpn-vrf", vrf_vars)

    def _setup_intf(
        self, device: ListElement, intf: ListElement, base_vars: list[str]
    ) -> None:
        """Configure network device interfaces. Validates that interfaces are compliant
        with existing resources allocated for existing interfaces on the network device

        Args:
            device (ListElement): Network device
            intf (ListElement): Interface list
            base_vars (list[str]): Base variables
        """
        self.ctx.log.info("Configuring interface: ", intf.name)
        template = Template(self.ctx.service)
        intf_vars = Variables(base_vars)
        intf_type, intf_id = self.network.get_intf_type_and_id(device.name, intf.name)
        self.network.validate_interface(device.name, intf, intf_type, intf_id)
        intf_vars.add("INTERFACE-NAME", intf.name)
        intf_vars.add("INTERFACE-TYPE", intf_type)
        intf_vars.add("INTERFACE-ID", intf_id)
        intf_vars.add("MTU", intf.mtu)
        intf_vars.add("PORT-MODE", intf.port_mode)
        intf_vars.add("ENCAPSULATION", "")
        intf_vars.add("VLAN-ID", "")
        intf_vars.add("INNER-VLAN-ID", "")
        intf_vars.add("IPV4-LOCAL-ADDRESS", "")
        intf_vars.add("IPV4-LOCAL-MASK", "")
        intf_vars.add("IPV6-LOCAL-PREFIX", "")
        if intf.ipv4_local_prefix:
            ip_address, ip_mask = self.network.get_ip_and_mask(intf.ipv4_local_prefix)
            intf_vars.add("IPV4-LOCAL-ADDRESS", ip_address)
            intf_vars.add("IPV4-LOCAL-MASK", ip_mask)

        if intf.ipv6_local_prefix:
            intf_vars.add("IPV6-LOCAL-PREFIX", intf.ipv6_local_prefix)

        template.apply("l3vpn-intf", intf_vars)

        if not intf.port_mode:
            for vlan_id in intf.vlan_id.as_list():
                intf_vars.add("VLAN-ID", vlan_id)
                template.apply("l3vpn-intf", intf_vars)

            if intf.inner_vlan_id:
                for inner_vlan_id in intf.inner_vlan_id.as_list():
                    intf_vars.add("INNER-VLAN-ID", inner_vlan_id)
                    template.apply("l3vpn-intf", intf_vars)

    def _setup_policy(self, intf: ListElement, ned_id: str, base_vars: list[str]) -> None:
        """Configure policy

        Args:
            intf (ListElement): Network device interface
            ned_id (str): NED ID of the device
            base_vars (list[str]): Base variables
        """
        self.ctx.log.info("Configuring policy for interface: ", intf.name)
        template_policy = Template(self.ctx.service)
        policy_vars = Variables(base_vars)
        if "cisco-ios-cli" in ned_id:
            cir = intf.cir * 1_000_000
        else:
            cir = intf.cir
        policy_vars.add("CIR", cir)
        template_policy.apply("l3vpn-policy", policy_vars)

    def _setup_static_routing(
        self, device: ListElement, static: PresenceContainer, base_vars: list[str]
    ) -> None:
        """Configure PE-CE static routing. For each static route, loop through all forwarding addresses, and subsequently through
        each interface on the device to ensure that each forwarding address falls within at least one of the IPv4 networks
        configured on the device interfaces

        Args:
            device (ListElement): Network device
            static (PresenceContainer): Static routing container
            base_vars (list[str]): Base variables
        """
        self.ctx.log.info("Configuring static routes")
        template_static = Template(self.ctx.service)
        static_vars = Variables(base_vars)
        static_vars.add("IPV4-DEST-PREFIX", "")
        static_vars.add("IPV4-FORWARDING", "")
        static_vars.add("IPV6-DEST-PREFIX", "")
        static_vars.add("IPV6-FORWARDING", "")

        # IPv4
        for prefix, intf in product(static.ipv4_destination_prefix, device.interface):
            static_vars.add("IPV4-DEST-PREFIX", prefix.ipv4_prefix)
            for forwarding_address in prefix.ipv4_forwarding.as_list():
                if intf.ipv4_local_prefix:
                    intf_network = ipaddress.ip_interface(
                        intf.ipv4_local_prefix
                    ).network

                    # TODO: Need to take into account having more than one interface per device as well as more than forwarding address per static route
                    if self.network.check_ip_host_in_network(forwarding_address, intf_network):
                        static_vars.add("IPV4-FORWARDING", forwarding_address)
                        template_static.apply("l3vpn-static", static_vars)
                    else:
                        raise Exception(
                            f"The ipv4-forwarding address {forwarding_address} for ipv4-destination-prefix {prefix.ipv4_prefix} on {device.name} does not fall within {intf_network}"
                        )

        # IPv6
        for prefix in static.ipv6_destination_prefix:
            static_vars.add("IPV6-DEST-PREFIX", prefix.ipv6_prefix)

            for forwarding_address in prefix.ipv6_forwarding.as_list():
                for intf in device.interface:
                    if intf.ipv6_local_prefix:
                        intf_network = ipaddress.ip_interface(
                            intf.ipv6_local_prefix
                        ).network

                        if self.network.check_ip_host_in_network(
                            forwarding_address, intf_network
                        ):
                            static_vars.add("IPV6-FORWARDING", forwarding_address)
                            template_static.apply("l3vpn-static", static_vars)

    def _setup_bgp_routing(
        self, device: ListElement, bgp: PresenceContainer, base_vars: list[str]
    ) -> None:
        """Configure PE-CE BGP routing

        Args:
            device (ListElement): Network device
            bgp (PresenceContainer): BGP routing container
            base_vars (list[str]): Base variables
        """
        self.ctx.log.info("Configuring BGP")
        template_bgp = Template(self.ctx.service)
        bgp_vars = Variables(base_vars)
        bgp_vars.add("IPv4-BGP-NEIGHBOR", "")
        bgp_vars.add("IPv6-BGP-NEIGHBOR", "")
        bgp_vars.add("BGP-NEIGHBOR-PASSWORD", "")
        bgp_vars.add("BGP-NEIGHBOR-ASN", bgp.asn)
        bgp_vars.add("BGP-ROUTE-POLICY-IN", bgp.route_policy_in)
        bgp_vars.add("BGP-ROUTE-POLICY-OUT", bgp.route_policy_out)

        for bgp_neighbor in bgp.ipv4_neighbor:
            bgp_vars.add("IPv4-BGP-NEIGHBOR", bgp_neighbor.address)
            bgp_vars.add("BGP-NEIGHBOR-PASSWORD", bgp_neighbor.password)
            template_bgp.apply("l3vpn-bgp", bgp_vars)

        for bgp_neighbor in bgp.ipv6_neighbor:
            bgp_vars.add("IPv6-BGP-NEIGHBOR", bgp_neighbor.address)
            bgp_vars.add("BGP-NEIGHBOR-PASSWORD", bgp_neighbor.password)
            template_bgp.apply("l3vpn-bgp", bgp_vars)

    def configure(self) -> None:
        """Docstring missing."""
        base_vars = []
        base_vars.append(("CUSTOMER-NAME", self.ctx.service.customer_name))
        base_vars.append(("SERVICE-ID", service_id := self.ctx.service.service_id))

        # Allocate VPN ID from the resource manager. If the user entered a
        # VPN ID into the service model, try and allocate that one, else,
        # generate a new one
        rma = Allocator(self.ctx.service)
        vpn_id = (
            rma
            .id(request_id=self.ctx.service.vpn_id)
            .pool('primary-vpn-pool')
            .allocate(self.ctx.service.service_id)
        )
        self.ctx.service.vpn_id = vpn_id
        self.ctx.log.info(f'Allocated VPN ID {vpn_id} from the resource manager')
        base_vars.append(("VPN-ID", vpn_id))
        base_vars.append(("INET", self.ctx.service.inet))
        base_vars.append(("MAX-ROUTES", self.ctx.service.max_routes))
        base_vars.append(("MAX-ROUTES-WARNING", self.ctx.service.max_routes_warning))
        base_vars.append(("AS-NUMBER", self.ctx.service.provider_edge.asn))

        for device in self.ctx.service.provider_edge.device:
            self.ctx.log.info("Configuring device: ", device.name)
            ned_id = self.device.get_device_ned_id(device.name)
            rd = f"{self.network.get_loopback_ip(device.name, 0)}:{vpn_id}"
            vrf = self.network.get_vrf_name(device.name, service_id, vpn_id)

            device_vars = base_vars + [
                ("DEVICE-NAME", device.name),
                ("RD", rd),
                ("VRF", vrf),
            ]

            self.ctx.log.info("Assigning RD: ", rd)
            self.ctx.log.info("Assigning VRF: ", vrf)

            self._setup_vrf(device, device_vars)

            for intf in device.interface:
                self._setup_intf(device, intf, device_vars)
                self._setup_policy(intf, ned_id, device_vars)

            if device.ce_routing.static:
                self._setup_static_routing(device, device.ce_routing.static, device_vars)

            if device.ce_routing.bgp:
                self._setup_bgp_routing(device, device.ce_routing.bgp, device_vars)
