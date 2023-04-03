# -*- mode: python; python-indent: 4 -*-
"""Docstring Missing."""


from .completion import InterfaceCompletion
from .l3vpn import L3vpn
from .network import Network
from .premod import PreMod
from ncs.application import Application,Service
from ncs.maagic import cd


class ServiceCallbacks(Service):
    """Docstring Missing."""

    @Service.pre_modification
    def cb_pre_modification(self, tctx, op, kp, root, proplist):
        """Docstring Missing."""
        self.log.info('Service premod(service=', kp, ')')
        if op == 2: return # nothing to do for 'Delete(2)' operation

        self.service = cd(root, kp)
        PreMod(self.log, root, self.service).fill()

    @Service.create
    def cb_create(self, tctx, root, service, proplist):
        """Docstring Missing."""
        self.log.info('Service create(service=', service._path, ')')
        L3vpn(self.log, root, service).configure()


# ---------------------------------------------
# COMPONENT THREAD THAT WILL BE STARTED BY NCS.
# ---------------------------------------------
class Main(Application):
    """Docstring Missing."""

    def setup(self):
        """Docstring Missing."""
        self.log.info('Main RUNNING')
        self.register_service('l3vpn-servicepoint', ServiceCallbacks)
        self.register_action('l3vpn-interface-name', InterfaceCompletion)

    def teardown(self):
        """Docstring Missing."""
        self.log.info('Main FINISHED')
