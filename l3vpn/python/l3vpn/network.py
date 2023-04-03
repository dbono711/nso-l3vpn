# -*- mode: python; python-indent: 4 -*-
"""Docstring Missing."""

import ipaddress
import re

from .device import Device
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
            deviceName (str): Network device hostname
            intfName (str): The complete network interface name

        Returns:
            list[str, str]: A network interface split into type and ID
        """
        ned = self.get_device_ned_id(deviceName)
        if "cisco-iosxr" in ned:
            return re.split(r'(^.*\B)', intfName)[1:]

    def get_next_subintf_id(self, deviceName: str, intfType: str) -> int:
        """Allocates the next available sub-interface ID on an interface

        Args:
            deviceName (str): Network device hostname
            intfType (str): The interface type (i.e., 'GigabitEthernet')

        Returns:
            int: next available sub-interface ID
        """
        ned = self.get_device_ned_id(deviceName)
        if "cisco-iosxr" in ned:
            sub_intf_list = cd(self.root, f'/devices/device{{{deviceName}}}/config/cisco-ios-xr:interface/{intfType}-subinterface/{intfType}')

        id_list = [int(x.id.split('.')[-1]) for x in sub_intf_list]
        self.log.info(f'Assigning sub-interface ID {(subt_intf_id := list(set(range(1, 2**8)) - set(id_list))[0])}')

        return subt_intf_id

    def get_loopback_ip(self, deviceName: str, loopbackNum: int) -> str:
        """Returns the IPv4 address of a given loopback number on a given network device

        Args:
            deviceName (str): Network device hostname
            loopbackNum (int): The number of the loopback interface on the network device

        Raises:
            Exception: An IPv4 address for the given loopback number does not exist on the network device
            Exception: The loopback number itself does not exist on the network device

        Returns:
            str: IPv4 Loopback address
        """        
        ned = self.get_device_ned_id(deviceName)
        if "cisco-iosxr" in ned:
            loopback_intf_list = cd(self.root, f'/devices/device{{{deviceName}}}/config/cisco-ios-xr:interface/Loopback')

        if loopbackNum in loopback_intf_list:
            loopback_ip = loopback_intf_list[loopbackNum].ipv4.address.ip

            if loopback_ip is None:
                raise Exception(f'An IPv4 address for Loopback{loopbackNum} does not exist on {deviceName}')
            else:
                return loopback_ip
        else:
            raise Exception(f'Loopback{loopbackNum} does not exist on {deviceName}')

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

    def get_ip_and_mask(self, prefix: str) -> list[str, str]:
        """Returns the IP address and netmask for a given IP prefix

        Args:
            prefix (str): IPv4/IPv6 prefix in CIDR notation

        Returns:
            list[str, str]: IP address and netmask
        """        
        return ipaddress.ip_interface(prefix).with_netmask.split('/')

    def check_ip_host_in_network(self, host: str, network: str) -> bool:
        """Validate whether an IP host is contained within an IP network

        Args:
            host (str): IP host address
            network (str): IP network to check within

        Returns:
            bool: Truthy statement on whether the host is contained within the network
        """        """Docstring Missing."""
        return ipaddress.ip_address(host) in ipaddress.ip_network(network)

    def __check_no_sub_interfaces_exist(self, subIntfIdList: list[str], deviceName: str, intfType: str, intfId: str) -> None:
        """Validate whether the existing interface we are trying to configure has any existing
        sub-interfaces configured on it when we are attempting a port-based configuration

        Args:
            subIntfIdList (list[str]): List of sub-interface ID's
            deviceName (str): Network device hostname
            intfType (str): The interface type (i.e., 'GigabitEthernet')
            intfId (str): The interface ID (i.e., '0/0/0/12')
        """        
        self.log.info('Checking for sub-interface conflicts')
        if len(subIntfIdList) > 0:
            self.log.info(subIntfIdList)
            raise Exception(f'{intfType}{intfId} on {deviceName} already has sub-interfaces configured, creating a "port-based" service is not allowed')

    def __check_interface_no_ip_exists(self, intfList: list[str], deviceName: str, intfType: str, intfId: str) -> None:
        """Validate that an existing list of interfaces does not already have an IP address configured

        Args:
            intfList (list[str]): List of interfaces on a network device
            deviceName (str): Network device hostname
            intfType (str): The interface type (i.e., 'GigabitEthernet')
            intfId (str): The interface ID (i.e., '0/0/0/12')
        """        
        self.log.info('Checking if interface has existing IP configuration')
        if intfList[intfId].ipv4.address.ip is not None:
            raise Exception(f'{intfType}{intfId} on {deviceName} already has an IPv4 address configured. Check to ensure it is not in use by another service')
        if len(intfList[intfId].ipv6.address.prefix_list) > 0:
            raise Exception(f'{intfType}{intfId} on {deviceName} already has an IPv6 address configured. Check to ensure it is not in use by another service')

    def __check_dot1q_encapsulation(self, subIntfIdList: list[str], deviceName: str, intfType: str, vlanIdList: list[str]) -> None:
        """Validate any existing dot1q encapsulation conflicts on a set of sub-interfaces

        Args:
            subIntfIdList (list[str]): List of sub-interface ID's
            deviceName (str): Network device hostname
            intfType (str): The interface type (i.e., 'GigabitEthernet')
            vlanIdList (list[str]): List of VLAN ID's being checked against
        """        
        self.log.info('Checking for VLAN encapsulation conflicts')
        for i in subIntfIdList:
            if any(item in vlanIdList for item in i.encapsulation.dot1q.vlan_id.as_list()):
                raise Exception(f'{intfType}{i.id} on {deviceName} already has a sub-interface configured with encapsulation {vlanIdList}')

    def __filter_sub_interfaces(self, subIntfList: list[str], intfId: str) -> list[str]:
        """Filter out configurable sub-interfaces from a list of sub-interfaces 

        Args:
            subIntfList (list[str]): List of sub-interfaces
            intfId (str): The interface ID (i.e., '0/0/0/12')
        """        
        sub_intf_id_list = []
        for i in subIntfList:
            if i.id.split(".")[0] == intfId:
                self.log.info(f'Filter is keeping sub-interface: {i.id}')
                sub_intf_id_list.append(i)

        return sub_intf_id_list
