# -*- mode: python; python-indent: 4 -*-
"""Docstring Missing."""

from .network import Network

class PreMod(Network):
    """Docstring Missing."""

    def __init__(self, log, root, service) -> None:
        self.log, self.root, self.service = log, root, service
    
    def fill(self):
        """_summary_
        """        
        # network = Network(self.log, root, self.service)
        for device in self.service.provider_edge.device:
            for intf in device.interface:
                if not intf.port_mode and not intf.efp_id:
                    self.log.info(f'Interface {intf.name} on {device.name} requires a sub-interface ID')
                    intf_type = self.get_intf_type_and_id(intf.name)[0]
                    intf.efp_id = self.get_next_subintf_id(device.name, intf_type)