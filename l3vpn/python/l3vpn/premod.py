# -*- mode: python; python-indent: 4 -*-
"""Docstring Missing."""

from ncs.log import Log
from ncs.maagic import ListElement, Root

from .network import Network


class PreMod(Network):
    """Docstring missing."""

    def __init__(self, log: Log, root: Root, service: ListElement) -> None:
        """Docstring missing."""
        self.log, self.root, self.service = log, root, service

    def fill(self) -> None:
        """Docstring missing."""
        for device in self.service.provider_edge.device:
            for intf in device.interface:
                if not intf.port_mode and not intf.efp_id:
                    self.log.info(
                        f"Interface {intf.name} on {device.name} requires a sub-interface ID"
                    )
                    intf_type, intf_id = self.get_intf_type_and_id(
                        device.name, intf.name
                    )
                    intf.efp_id = self.get_next_subintf_id(
                        device.name, intf_type, intf_id
                    )
