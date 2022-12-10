# -*- mode: python; python-indent: 4 -*-
"""Docstring Missing."""

import ipaddress
import re

from l3vpn.device import Device
from ncs.maagic import cd, ListElement


class Network(Device):
    """Docstring Missing."""

    def get_vrf_name(self, deviceName: str, name: str, vpn: int) -> str:
        """Formats the Virtual Routing & Forwarding (VRF) name for the MPLS L3VPN using
        a combination of name: str and vpn: int. Accomodates for nuances in character and
        length limitation in Cisco IOS XR.

        Args:
            deviceName (str): Network device hostname
            name (str): A name for the VRF
            vpn (int): A Virtual Private Network (VPN) identifier

        Returns:
            str: VRF name formatted as a combination of name: str and vpn: int
        """        
        ned = self.get_device_ned_id(deviceName)
        if "cisco-iosxr" in ned:
            name = re.sub(r'[\.\(\)\, ]', '_', name)[:32] # accomodate for Cisco IOS XR character/length limitations
            
        return f'{name}:{vpn}'
    
    def get_intf_type_and_id(self, deviceName: str, intfName: str) -> list[str, str]:
        """Splits a complete network interface into type and ID. For example, for Cisco interface
        'GigabitEthernet0/0/0/12', this method will return ['GigabitEthernet', '0/0/0/12']

        Args:
            intfName (str): The complete network interface name

        Returns:
            list[str, str]: A network interface split into type and ID
        """
        ned = self.get_device_ned_id(deviceName)
        if "cisco-iosxr" in ned:
            return re.split(r'(^.*\B)', intfName)[1:]
    
    def validate_interface(self, deviceName: str, intf: ListElement, intfType: str, intfId: str) -> None:
        """Validates that a given interface on a device does not;
            a) contain any sub-interfaces if the interface is configured for port-mode
            b) does not already contain an IP address
            c) does not have an overlap in dot1q encapsulation if the interface is not configured for port mode

        Args:
            deviceName (str): Network device hostname
            intf (ListElement): Network device interface as an NCS Maagic ListElement
            intfType (str): The interface type (i.e., 'GigabitEthernet')
            intfId (str): The interface ID (i.e., '0/0/0/12')
        """        
        self.log.info(f'Checking interface {intfType}{intfId} on {deviceName}')
        ned = self.get_device_ned_id(deviceName)
        if "cisco-iosxr" in ned:
            intf_list = cd(self.root, f'/devices/device{{{deviceName}}}/config/cisco-ios-xr:interface/{intfType}')
            sub_intf_list = cd(self.root, f'/devices/device{{{deviceName}}}/config/cisco-ios-xr:interface/{intfType}-subinterface/{intfType}')
        
        sub_intf_id_list = self.__filter_sub_interfaces(sub_intf_list, intfId)
        if intf.port_mode:
            self.__check_no_sub_interfaces_exist(sub_intf_id_list, deviceName, intfType, intfId)
            self.__check_interface_no_ip_exists(intf_list, deviceName, intfType, intfId)
        else:
            self.__check_dot1q_encapsulation(sub_intf_list, deviceName, intfType, intf.vlan_id.as_list())



    def __check_no_sub_interfaces_exist(self, subIntfIdList: list[str], deviceName: str, intfType: str, intfId: str) -> None:
        """Docstring Missing."""
        self.log.info('Checking for sub-interface conflicts')
        if len(sub_intf_id_list) > 0:
            self.log.info(sub_intf_id_list)
            raise Exception(f'{intf_type}{intf_id} on device {device_name} already has sub-interfaces configured, creating a "port-based" service is not allowed')

    def __check_interface_no_ip_exists(self, intf_list, device_name, intf_type, intf_id):
        """Docstring Missing."""
        self.log.info('Checking if interface has existing IP configuration')
        if intf_list[intf_id].ipv4.address.ip is not None:
            raise Exception(f'{intf_type}{intf_id} on device {device_name} already has an IPv4 address configured. Check to ensure it is not in use by another service')
        if len(intf_list[intf_id].ipv6.address.prefix_list) > 0:
            raise Exception(f'{intf_type}{intf_id} on device {device_name} already has an IPv6 address configured. Check to ensure it is not in use by another service')

    def __check_dot1q_encapsulation(self, sub_intf_list, device_name, intf_type, vlan_id_list):
        """Docstring Missing."""
        self.log.info('Checking for VLAN encapsulation conflicts')
        for i in sub_intf_list:
            if any(item in vlan_id_list for item in i.encapsulation.dot1q.vlan_id.as_list()):
                raise Exception(f'{intf_type}{i.id} on device {device_name} already has a sub-interface configured with encapsulation {vlan_id_list}')

    def __filter_sub_interfaces(self, sub_intf_list, intf_id):
        """Docstring Missing."""
        sub_intf_id_list = []
        for i in sub_intf_list:
            if i.id.split(".")[0] == intf_id:
                self.log.info(f'Filter is keeping sub-interface: {i.id}')
                sub_intf_id_list.append(i)

        return sub_intf_id_list
    
    def get_ip_and_mask(self, ip_prefix):
        """Docstring Missing."""
        return ipaddress.ip_interface(ip_prefix).with_netmask.split('/')

    def get_loopback_ip(self, device_name, loopback_num):
        """Docstring Missing."""
        ned = self.get_device_ned_id(device_name)
        if "cisco-iosxr" in ned:
            loopback_intf_list = cd(self.root, f'/devices/device{{{device_name}}}/config/cisco-ios-xr:interface/Loopback')

        if loopback_num in loopback_intf_list:
            loopback_ip = loopback_intf_list[loopback_num].ipv4.address.ip
            if loopback_ip is None:
                raise Exception(f'An IPv4 address for Loopback0 does not exist on {device_name}')
            else:
                return loopback_ip
        else:
            raise Exception(f'Loopback0 does not exist on {device_name}')

    def get_next_subintf_id(self, device_name, intf_type):
        """Docstring Missing."""
        ned = self.get_device_ned_id(device_name)
        if "cisco-iosxr" in ned:
            sub_intf_list = cd(self.root, f'/devices/device{{{device_name}}}/config/cisco-ios-xr:interface/{intf_type}-subinterface/{intf_type}')

        id_list = [int(x.id.split('.')[-1]) for x in sub_intf_list]
        self.log.info(f'Assigning sub-interface ID {(efp_id := list(set(range(1, 2**16)) - set(id_list))[0])}')

        return efp_id

    def check_ip_host_in_network(self, host, network):
        """Docstring Missing."""
        return ipaddress.ip_address(host) in ipaddress.ip_network(network)
