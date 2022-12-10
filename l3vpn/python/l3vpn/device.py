# -*- mode: python; python-indent: 4 -*-
"""Docstring Missing."""

import ncs


class Device:
    """Docstring Missing."""

    def __init__(self, log, root, service):
        """Docstring Missing."""
        self.log = log
        self.root = root
        self.service = service

    def get_device_model(self, deviceName: str) -> str:
        """Return the device model, as a string, for a given device

        Args:
            deviceName (str): Network device hostname

        Returns:
            str: Network device model
        """  
        return self.root.devices.device[deviceName].platform.model

    def get_device_ned_id(self, deviceName: str) -> str:
        """Return the device Network Element Driver (NED) ID, as a string,
        for a given device

        Args:
            deviceName (str): Network device hostname

        Returns:
            str: Network Element Driver (NED) ID
        """        
        device = ncs.maagic.cd(self.root, f'/ncs:devices/ncs:device/{deviceName}')

        return ncs.application.get_ned_id(device)
