# -*- mode: python; python-indent: 4 -*-
"""Docstring Missing."""

from ncs.log import Log
from ncs.maagic import cd,Root,ListElement
from ncs.application import get_ned_id


class Device:
    """Docstring Missing."""

    def __init__(self, log: Log, root: Root, service: ListElement) -> None:
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
        device = cd(self.root, f'/ncs:devices/ncs:device/{deviceName}')

        return get_ned_id(device)
