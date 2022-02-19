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

    def get_device_model(self, device_name):
        """Docstring Missing."""
        return self.root.devices.device[device_name].platform.model

    def get_device_ned_id(self, device_name):
        """Docstring Missing."""
        dev_path = f"/ncs:devices/ncs:device/{device_name}"
        dev = ncs.maagic.cd(self.root, dev_path)
        return ncs.application.get_ned_id(dev)
