# -*- mode: python; python-indent: 4 -*-
"""Docstring Missing."""

from .context import ServiceContext
from .network import Network


class PreMod:
    """Docstring missing."""

    def __init__(self, ctx: ServiceContext) -> None:
        """Docstring missing."""
        self.ctx = ctx
        self.network = Network(ctx)

    def fill(self) -> None:
        """Docstring missing."""
        for device in self.ctx.service.provider_edge.device:
            for intf in device.interface:
                if not intf.port_mode and not intf.efp_id:
                    self.ctx.log.info(
                        f"Interface {intf.name} on {device.name} requires a sub-interface ID"
                    )
                    intf_type, intf_id = self.network.get_intf_type_and_id(
                        device.name, intf.name
                    )
                    intf.efp_id = self.network.get_next_subintf_id(
                        device.name, intf_type, intf_id
                    )
