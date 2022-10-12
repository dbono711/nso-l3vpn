# -*- mode: python; python-indent: 4 -*-
"""Docstring Missing."""

from ncs.dp import Action
from _ncs.dp import action_reply_completion
from ncs.maapi import Maapi
from ncs.maagic import cd, get_root, get_trans


def get_root_uinfo(uinfo):
    """Docstring Missing."""
    trans = Maapi().attach(uinfo.actx_thandle, usid=uinfo.usid)
    return get_root(trans)

def xpath_eval(node, xpath):
    """Docstring Missing."""
    return get_trans(node).xpath_eval_expr(xpath, None, '/')

def get_device(root, pe_path, log):
    """Docstring Missing."""
    log.info(f'Device Keypath: {pe_path}')
    dev_name = cd(root, f'{pe_path}/name')
    return ServiceDevice(root, dev_name, log)


class ServiceDevice:
    """Docstring Missing."""

    def __init__(self, root, dev_name, log):
        """Docstring Missing."""
        self._log = log
        self._log.info(f'Device: {dev_name}')
        self._device = cd(root, f'/ncs:devices/ncs:device{{{dev_name}}}')

    @property
    def ned_id(self):
        """Docstring Missing."""
        ned_type = str(cd(self._device, 'device-type/ne-type'))
        ned_id_str = str(cd(self._device, f'device-type/{ned_type}/ned-id'))
        self._log.info(f'Device.ned_id: {ned_id_str}')
        
        return ned_id_str

    @property
    def intf_list(self):
        """Docstring Missing."""
        if '-iosxr-' in self.ned_id:
            return self._xr_if_list()
        
        elif '-ios-' in self.ned_id:
            return self._ios_if_list()
        
        elif '-junos-' in self.ned_id:
            return self._junos_if_list()

    def _xr_if_list(self):
        """Docstring Missing."""
        if_list = []
        for intf_type in ['GigabitEthernet', 'TenGigE', 'Loopback']:
            for intf in cd(self._device, f'config/cisco-ios-xr:interface/{intf_type}'):
                if_list.append(f'{intf_type}{intf.id}')
                # self._log.info(f'Device._iosxr_if_list: {if_list[-1]}')
        self._log.info(f'Device._iosxr_if_list: returning {if_list}')
        
        return if_list

    def _ios_if_list(self):
        """Docstring Missing."""
        if_list = []
        for intf_type in ['GigabitEthernet', 'TenGigabitEthernet', 'Loopback']:
            for intf in cd(self._device, f'config/ios:interface/{intf_type}'):
                if_list.append(f'{intf_type}{intf.name}')
                # self._log.info(f'Device._ios_if_list: {if_list[-1]}')
        self._log.info(f'Device._ios_if_list: returning {if_list}')
        
        return if_list

    def _junos_if_list(self):
        """Docstring Missing."""
        if_list = []
        for intf in cd(self._device, 'config/junos:configuration/interfaces/interface'):
            if_list.append(intf.name)
            # self._log.info(f'Device._junos_if_list: {if_list[-1]}')
        self._log.info(f'Device._junos_if_list: returning {if_list}')
        
        return if_list


class InterfaceCompletion(Action):
    """Docstring Missing."""

    def cb_completion(self, uinfo, cli_style, token, completion_char, kp, cmdpath, cmdparam_id, simpleType, extra):
        """Displays list of possible interface completions for a given device."""

        self.log.info('=' * 80)
        self.log.info(f'Completion-Actionpoint: {self.actionpoint}')
        root = get_root_uinfo(uinfo)
        completion_list = []

        if cmdparam_id.startswith('provideredge-'):
            self.log.info(f'Completion_id: {cmdparam_id}')
            # When receiving an HKeypathRef (kp) object as on argument in a callback method, the underlying object is only
            # borrowed, so this particular instance is only valid inside that callback method. If one, for some reason, would
            # like to keep the HKeypathRef object 'alive' for any longer than that, use dup() or dup_len() to get a copy of it,
            # where, 'len' duplicates the first len elements of this hkeypath (kp)
            site_keypath = str(kp.dup_len(6)) # In this case, our device in the service model is 6 elements deep
            device = get_device(root, site_keypath, self.log)

            for intf in device.intf_list:
                completion_list.append((0, intf, ' '))

        else:
            self.log.info(f'No matching completion_id: {cmdparam_id}')

        action_reply_completion(uinfo, completion_list)
