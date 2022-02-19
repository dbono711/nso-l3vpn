# -*- mode: python; python-indent: 4 -*-
"""Docstring Missing."""

import ncs
import re
import ipaddress

from l3vpn.device import Device


class Network(Device):
    """Docstring Missing."""

    _ipv4_size = 32
    _ipv4_max = 2 ** _ipv4_size - 1

    def get_ip_and_mask(self, ip_prefix):
        """Docstring Missing."""
        return ipaddress.ip_interface(ip_prefix).with_netmask.split("/")

    def get_loopback_ip(self, device_name, loopback_num):
        """Docstring Missing."""
        root_device = self.root.devices.device[device_name]
        ned = self.get_device_ned_id(device_name)
        if "cisco-iosxr" in ned:
            intf = root_device.config.cisco_ios_xr__interface
            if loopback_num in intf["cisco-ios-xr:Loopback"]:
                loopback_ip = intf["cisco-ios-xr:Loopback"][loopback_num].ipv4.address.ip
                if loopback_ip is None:
                    raise Exception(
                        f'An IPv4 address for Loopback0 does not exist on {device_name}. Cannot proceed with service configuration')
                else:
                    return loopback_ip
            else:
                raise Exception(
                    f'Loopback0 does not exist on {device_name}. Cannot proceed with service configuration')

    def get_next_subintf_id(self, device_name, intf):
        """Docstring Missing."""
        intf_type, intf_id = re.split(r'(^.*\B)', intf.name)[1:]

        # Get the list of sub-interface objects from the device
        sub_intf_list = ncs.maagic.cd(
            self.root, f'/devices/device{{{device_name}}}/config/cisco-ios-xr:interface/{intf_type}-subinterface/{intf_type}')

        # Loop through sub-interface objects and extract the id
        id_list = []
        for sub_intf in sub_intf_list:
            id_list.append(int(sub_intf.id.split('.')[-1]))

        # Subtract list of currently assigned subinterface id from range of valid id, and assign first available id
        efp_id = list(set(range(1, 2**16)) - set(id_list))[0]
        self.log.info(
            f"Assigning sub-interface ID {efp_id} for {device_name} {intf.name}")

        return efp_id

    def check_allowed_interface(self, device, intf_type, intf_id, intf_port_mode):
        """Docstring Missing."""
        root_device = self.root.devices.device[device.device_name]
        ned = self.get_device_ned_id(device.device_name)
        if intf_type == "GigabitEthernet":
            intf_list = root_device.config.cisco_ios_xr__interface.GigabitEthernet
            sub_intf_list = root_device.config.cisco_ios_xr__interface.GigabitEthernet_subinterface.GigabitEthernet
        if intf_type == "TenGigE":
            intf_list = root_device.config.cisco_ios_xr__interface.TenGigE
            sub_intf_list = root_device.config.cisco_ios_xr__interface.TenGigE_subinterface.TenGigE
        if not intf_port_mode:
            intf_port_type = "vlan-based"
        else:
            intf_port_type = "port-based"

        if "cisco-iosxr" in ned:
            for intf in device.interface:
                self.log.info(
                    f'Checking {intf_type}{intf_id} ({intf_port_type}) on {device.device_name}')
                sub_intf_id_list = self.__filter_sub_interfaces(
                    sub_intf_list, intf_id)
                if intf_port_mode:
                    self.__check_no_sub_interfaces_exist(
                        sub_intf_id_list, device.device_name, intf_type, intf_id)
                    self.__check_interface_no_ip_exists(
                        intf_list, device.device_name, intf_type, intf_id)
                else:
                    self.__check_dot1q_encapsulation(
                        sub_intf_list, device.device_name, intf_type, intf.vlan_id.as_list())

    def check_host_in_network(self, host, network):
        """Docstring Missing."""
        return ipaddress.ip_address(host) in ipaddress.ip_network(network)

    def __check_no_sub_interfaces_exist(self, sub_intf_id_list, device_name, intf_type, intf_id):
        """Docstring Missing."""
        self.log.info('Checking for sub-interface conflicts')
        if len(sub_intf_id_list) > 0:
            self.log.info(sub_intf_id_list)
            raise Exception(
                f'{intf_type}{intf_id} on device {device_name} already has sub-interfaces configured, creating a "port-based" service is not allowed')

    def __check_interface_no_ip_exists(self, intf_list, device_name, intf_type, intf_id):
        """Docstring Missing."""
        self.log.info('Checking if interface has existing IP configuration')
        if intf_list[intf_id].ipv4.address.ip is not None:
            raise Exception(
                f'{intf_type}{intf_id} on device {device_name} already has an IPv4 address configured. Check to ensure it is not in use by another service')
        if len(intf_list[intf_id].ipv6.address.prefix_list) > 0:
            raise Exception(
                f'{intf_type}{intf_id} on device {device_name} already has an IPv6 address configured. Check to ensure it is not in use by another service')

    def __check_dot1q_encapsulation(self, sub_intf_list, device_name, intf_type, vlan_id_list):
        """Docstring Missing."""
        self.log.info('Checking for VLAN encapsulation conflicts')
        for i in sub_intf_list:
            if any(item in vlan_id_list for item in i.encapsulation.dot1q.vlan_id.as_list()):
                raise Exception(
                    f'{intf_type}{i.id} on device {device_name} already has a sub-interface configured with encapsulation {vlan_id_list}')

    def __filter_sub_interfaces(self, sub_intf_list, intf_id):
        """Docstring Missing."""
        sub_intf_id_list = []
        for i in sub_intf_list:
            if i.id.split(".")[0] == intf_id:
                self.log.info(f'Filter is keeping sub-interface: {i.id}')
                sub_intf_id_list.append(i)

        return sub_intf_id_list
