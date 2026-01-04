# -*- mode: python; python-indent: 4 -*-
"""Docstring Missing."""


from ncs.application import Application, Service
from ncs.maagic import cd

from .completion import InterfaceCompletion
from .context import ServiceContext
from .l3vpn import L3vpn
from .premod import PreMod


class ServiceCallbacks(Service):
    """Docstring Missing."""

    @Service.pre_modification
    def cb_pre_modification(self, tctx, op, kp, root, proplist):
        """Docstring Missing."""
        self.log.info(f"Service premod(service={kp})")
        service = cd(root, kp)
        ctx = ServiceContext(log=self.log, root=root, service=service)

        if op == 2:
            return  # nothing to do for 'Delete(2)' operation

        PreMod(ctx).fill()

    @Service.create
    def cb_create(self, tctx, root, service, proplist):
        """Docstring Missing."""
        self.log.info(f"Service create(service={service._path})")
        ctx = ServiceContext(log=self.log, root=root, service=service)
        L3vpn(ctx).configure()


class Main(Application):
    """Docstring Missing."""

    def setup(self):
        """Docstring Missing."""
        self.log.info("Main RUNNING")
        self.register_service("l3vpn-servicepoint", ServiceCallbacks)
        self.register_action("l3vpn-interface-name", InterfaceCompletion)

    def teardown(self):
        """Docstring Missing."""
        self.log.info("Main FINISHED")
