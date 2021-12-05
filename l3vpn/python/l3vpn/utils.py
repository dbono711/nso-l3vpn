# -*- mode: python; python-indent: 4 -*-
import ncs
import ipaddress


class Device:
    def __init__(self, log, root, service):
        self.log = log
        self.root = root
        self.service = service

    def get_device_ned_id(self, device_name):
        dev_path = f"/ncs:devices/ncs:device/{device_name}"
        dev = ncs.maagic.cd(self.root, dev_path)
        return ncs.application.get_ned_id(dev)

    def get_device_model(self, device_name):
        return root.devices.device[name].platform.model


class Network:
    def __init__(self, log, root, service):
        self.log = log
        self.root = root
        self.service = service
        self._ipv4_size = 32
        self._ipv4_max = 2 ** self._ipv4_size - 1

    def get_ipv4_ip_and_netmask(self, ip_prefix):
        return (ip_prefix.split("/")[0], ipaddress.IPv4Network(bytes(ip_prefix, 'utf-8').decode('UTF-8', 'ignore'), strict=False).netmask)

    def get_loopback0_ip(self, device_name):
        device = self.root.devices.device[device_name]
        ned = Device.get_device_ned_id(self, device_name)
        if "cisco-iosxr" in ned:
            intf = device.config.cisco_ios_xr__interface
            if "0" in intf["cisco-ios-xr:Loopback"]:
                loopback_ip = intf["cisco-ios-xr:Loopback"]["0"].ipv4.address.ip
                if loopback_ip is None:
                    raise Exception(f"An IPv4 address for Loopback0 does not exist on {device_name}. Cannot proceed with service configuration")
                else:
                    return loopback_ip
            else:
                raise Exception(f"Loopback0 does not exist on {device_name}. Cannot proceed with service configuration")

    # def getIpAddress(addr):
    #     """Return the IP part of an IP Prefix ('IP/Network') string"""
    #     parts = addr.split('/')
    #     return parts[0]

    # def getIpNetwork(addr):
    #     """Return the Network part of an IP Prefix ('IP/Network') string"""
    #     parts = addr.split('/')
    #     return parts[1]

    # def getNetMask(addr):
    #     """Return the Network Mask from an IP Prefix ('IP/Network') string"""
    #     return ipv4_int_to_str(prefix_to_netmask(int(getIpPrefix(addr))))

    # def getNextIPV4Address(addr):
    #     """Get the next succeeding IP address...hm..."""
    #     i = ipv4_str_to_int(getIpAddress(addr)) + 1
    #
    #     if i > _ipv4_max:
    #         raise ValueError("next IPV4 address out of bound")
    #     else:
    #         if (i & 0xff) == 255:
    #             i += 2
    #
    #     return ipv4_int_to_str(i)

    # def prefixToWildcardMask(prefix):
    #     """Transform a prefix (as string) to a netmask (as a string)."""
    #     return ipv4_int_to_str(prefix_to_netmask(int(prefix)))

    # def prefix_to_netmask(prefix):
    #     """Transform an IP integer prefix to a netmask integer."""
    #     global _ipv4_size
    #     global _ipv4_max
    #     if (prefix >= 0) and (prefix <= _ipv4_size):
    #         return _ipv4_max ^ (2 ** (_ipv4_size - prefix) - 1)
    #     else:
    #         raise ValueError('IPV4 prefix out of bound')

    # def ipv4_str_to_int(addr):
    #     """Transform an IPV4 address string to an integer."""
    #     parts = addr.split('.')
    #     if len(parts) == 4:
    #         return (int(parts[0]) << 24) | (int(parts[1]) << 16) | \
    #             (int(parts[2]) << 8) | int(parts[3])
    #     else:
    #         raise ValueError('wrong format of IPV4 string')

    # def ipv4_int_to_str(value):
    #     """Transform an IP integer to a string"""
    #     global _ipv4_max
    #     if (value >= 0) and (value <= _ipv4_max):
    #         return '%d.%d.%d.%d' % (value >> 24, (value >> 16) & 0xff,
    #                                 (value >> 8) & 0xff, value & 0xff)
    #     else:
    #         raise ValueError('IPV4 value out of bound')

    def check_interface_config_allowed(self, device):
        if device.interface.GigabitEthernet_iosxr is not None and len(device.interface.GigabitEthernet_iosxr) > 0:
            self.log.info(f"Checking 'GigabitEthernet' interfaces on {device.device_name}")
            interface_type = "GigabitEthernet"
            interface_list = self.root.devices.device[device.device_name].config.cisco_ios_xr__interface.GigabitEthernet  # Interfaces on device
            sub_interface_list = self.root.devices.device[device.device_name].config.cisco_ios_xr__interface.GigabitEthernet_subinterface.GigabitEthernet  # Sub-interfaces on device
            for intf in device.interface.GigabitEthernet_iosxr:
                interface_id = intf.interface_id
                sub_interface_list = self.filter_sub_interfaces(sub_interface_list, interface_id)
                if intf.port_mode:
                    self.check_no_sub_interfaces_exist(sub_interface_list, device.device_name, interface_type, interface_id)
                    self.check_interface_no_ip_exists(interface_list, device, interface_type, interface_id)
                else:
                    for vlan_id in intf.vlan_id.as_list():
                        self.check_dot1q_encapsulation(sub_interface_list, device.device_name, interface_type, vlan_id)

        if device.interface.TenGigabitEthernet_iosxr is not None and len(device.interface.TenGigabitEthernet_iosxr) > 0:
            self.log.info(f"Checking 'TenGigabitEthernet' interfaces on {device.device_name}")
            interface_type = "TenGigE"
            interface_list = self.root.devices.device[device.device_name].config.cisco_ios_xr__interface.TenGigE  # Interfaces on device
            sub_interface_list = self.root.devices.device[device.device_name].config.cisco_ios_xr__interface.TenGigE_subinterface.TenGigE  # Sub-interfaces on device
            for intf in device.interface.TenGigabitEthernet_iosxr:
                interface_id = intf.interface_id
                sub_interface_list = self.filter_sub_interfaces(sub_interface_list, interface_id)
                if intf.port_mode:
                    self.check_no_sub_interfaces_exist(sub_interface_list, device.device_name, interface_type, interface_id)
                    self.check_interface_no_ip_exists(interface_list, device, interface_type, interface_id)
                else:
                    for vlan_id in intf.vlan_id.as_list():
                        self.check_dot1q_encapsulation(sub_interface_list, device.device_name, interface_type, vlan_id)

    def check_dot1q_encapsulation(self, sub_interface_list, device_name, interface_type, vlan_id):
        for i in sub_interface_list:
            self.log.info(f"Checking dot1q encapsulations on interface {i.id}")
            vpn_id = i.id.split('.')[1]
            if int(vpn_id) != self.service.vpn_id and vlan_id in i.encapsulation.dot1q.vlan_id :
                raise Exception(f"Encapsulation with dot1q vlan-id {vlan_id} already exists on device {device_name} sub-interface {interface_type} {i.id}")

    def check_no_sub_interfaces_exist(self, sub_interface_list, device_name, interface_type, interface_id):
        self.log.info(f"Checking that no sub-interfaces exist, list is {len(sub_interface_list)} long")
        if len(sub_interface_list) > 0:
            for i in sub_interface_list:
                self.log.info(f"Checking interface {i.id}")
            raise Exception(f"Port {interface_type} {interface_id} on device {device_name} already has sub-interfaces configured, creating the service with 'port-mode = true' is not allowed")

    def check_interface_no_ip_exists(self, interface_list, device, interface_type, interface_id):
        self.log.info("Checking if interface has existing IP configuration")
        if interface_list[interface_id].ipv4.address.ip is not None:
            raise Exception(f"Port {interface_type} {interface_id} on device {device.device_name} is already configured with an IPv4 address")
        if len(interface_list[interface_id].ipv6.address.prefix_list) > 0:
            raise Exception(f"Port {interface_type} {interface_id} on device {device.device_name} is already configured with an IPv6 address")

    def filter_sub_interfaces(self, sub_interface_list, interface_id):
        new_list = []
        for i in sub_interface_list:
            if i.id.split(".")[0] == interface_id:
                self.log.info(f"Filter is keeping sub-interface {i.id}")
                new_list.append(i)
        return new_list
