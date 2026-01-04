# -*- mode: python; python-indent: 4 -*-
"""Docstring Missing."""

from ncs.application import get_ned_id
from ncs.maagic import cd
from .context import ServiceContext


class Device:
    """Docstring Missing."""

    def __init__(self, ctx: ServiceContext) -> None:
        self.ctx = ctx

    def get_device_model(self, deviceName: str) -> str:
        """Return the device model, as a string, for a given device

        Args:
            deviceName (str): Network device hostname

        Returns:
            str: Network device model
        """
        return self.ctx.root.devices.device[deviceName].platform.mode

    def get_device_ned_id(self, deviceName: str) -> str:
        """Return the device Network Element Driver (NED) ID, as a string,
        for a given device

        Args:
            deviceName (str): Network device hostname

        Returns:
            str: Network Element Driver (NED) ID
        """
        device = cd(self.ctx.root, f"/ncs:devices/ncs:device/{deviceName}")

        return get_ned_id(device)
