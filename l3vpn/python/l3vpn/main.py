# -*- mode: python; python-indent: 4 -*-
import ncs
import re

from ncs.application import Service
from l3vpn.completion import InterfaceCompletion
from l3vpn.utils import Device
from l3vpn.l3vpn import L3vpn


class ServiceCallbacks(Service):
    @Service.create
    def cb_create(self, tctx, root, service, proplist):
        self.log.info('@ Service create(service=', service._path, ') @')
        L3vpn(self.log, root, service).configure()

    @Service.pre_modification
    def cb_pre_modification(self, tctx, op, kp, root, proplist):
        if op == 2:  # Nothing to do for a 'Delete' operation
            return

        self.log.info('@ Service premod(service=', kp, ') @')
        self.service = ncs.maagic.cd(root, kp)
        self.device = Device(self.log, root, self.service)
        for device in self.service.device:
            ned = self.device.get_device_ned_id(device.device_name)

            self.log.info(f"Checking resources for {device.device_name} with ned {ned}")
            for intf in device.interface:
                intf_type, intf_id = re.split(r'(^.*\B)', intf.name)[1:]

                if not intf.port_mode and not intf.efp_id:
                    id_list = []

                    # Get the list of sub-interface objects
                    sub_intf_list = ncs.maagic.cd(root, f'/devices/device{{{device.device_name}}}/config/cisco-ios-xr:interface/{intf_type}-subinterface/{intf_type}')

                    # Loop through subinterface objects, extract the sub-interface_id and convert to integer
                    for sub_intf in sub_intf_list:
                        id_list.append(int(sub_intf.id.split('.')[-1]))

                    # Subtract list of currently assigned subinterface_id from range of valid id, and assign first available id
                    intf.efp_id = list(set(range(1, 2**16)) - set(id_list))[0]
                    self.log.info(f"Assigning EFP ID {intf.efp_id} for {device.device_name} {intf.name}")


# ---------------------------------------------
# COMPONENT THREAD THAT WILL BE STARTED BY NCS.
# ---------------------------------------------
class Main(ncs.application.Application):
    def setup(self):
        self.log.info('Main RUNNING')
        self.register_service('l3vpn-servicepoint', ServiceCallbacks)
        self.register_action('l3vpn-interface-name', InterfaceCompletion)

    def teardown(self):
        self.log.info('Main FINISHED')
