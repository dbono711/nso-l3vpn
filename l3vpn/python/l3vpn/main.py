# -*- mode: python; python-indent: 4 -*-
"""Docstring Missing."""

import ncs
import re

from ncs.application import Service
from l3vpn.completion import InterfaceCompletion
from l3vpn.network import Network
from l3vpn.l3vpn import L3vpn


class ServiceCallbacks(Service):
    """Docstring Missing."""

    @Service.create
    def cb_create(self, tctx, root, service, proplist):
        """Docstring Missing."""
        self.log.info('Service create(service=', service._path, ')')
        L3vpn(self.log, root, service).configure()

    @Service.pre_modification
    def cb_pre_modification(self, tctx, op, kp, root, proplist):
        """Docstring Missing."""
        self.log.info('Service premod(service=', kp, ')')

        # Nothing to do for a 'Delete' operation
        if op == 2:
            return

        self.service = ncs.maagic.cd(root, kp)
        network = Network(self.log, root, self.service)
        for device in self.service.device:
            for intf in device.interface:
                self.log.info(
                    f'Checking interface resources on {device.device_name} against our service')
                intf_type, intf_id = re.split(r'(^.*\B)', intf.name)[1:]
                if not intf.port_mode and not intf.efp_id:
                    self.log.info(
                        f'Interface {intf.name} on {device.device_name} requires a sub-interface ID')
                    intf.efp_id = network.get_next_subintf_id(
                        device.device_name, intf)


# ---------------------------------------------
# COMPONENT THREAD THAT WILL BE STARTED BY NCS.
# ---------------------------------------------
class Main(ncs.application.Application):
    """Docstring Missing."""

    def setup(self):
        """Docstring Missing."""
        self.log.info('Main RUNNING')
        self.register_service('l3vpn-servicepoint', ServiceCallbacks)
        self.register_action('l3vpn-interface-name', InterfaceCompletion)

    def teardown(self):
        """Docstring Missing."""
        self.log.info('Main FINISHED')
