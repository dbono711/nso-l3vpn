## NSO Service Package
l3vpn

## Use Case Identifier
UC-01 IPv4, three UNI, Tagged and Un-Tagged

## Description
This test executes the CRUD life cycle for an L3VPN service instance with **IPv4** connectivity between **three (3) UNI**, using the ```l3vpn``` service package, in accordance with the [NSO Package Testing Framework](../../tests/README.md) contained in this repository

The NSO CLI used to generate the respective CREATE (```create.xml```) and UPDATE (```update.xml```) XML files can be found below

## NSO Service Configuration (```create.xml```)

```
set services l3vpn Disneyland "Mickey Mouse" 1 cir 123 inet IPv4
set services l3vpn Disneyland "Mickey Mouse" 1 device iosxr-0 redistribution-protocol [ connected ] interface TenGigabitEthernet-iosxr 2/0 port-mode true ipv4-local-prefix 10.10.10.1/29
set services l3vpn Disneyland "Mickey Mouse" 1 device iosxr-1 redistribution-protocol [ connected ] interface TenGigabitEthernet-iosxr 2/0 port-mode true ipv4-local-prefix 10.10.10.9/29
set services l3vpn Disneyland "Mickey Mouse" 1 device iosxr-2 redistribution-protocol [ connected ] interface GigabitEthernet-iosxr 2/0 port-mode false encapsulation dot1q vlan-id [ 100 ] ipv4-local-prefix 10.10.10.17/29
```

## NSO Service Configuration (```update.xml```)

```
set services l3vpn Disneyland "Mickey Mouse" 1 cir 456 inet IPv4
set services l3vpn Disneyland "Mickey Mouse" 1 device iosxr-0 redistribution-protocol [ connected ] interface TenGigabitEthernet-iosxr 2/1 port-mode true ipv4-local-prefix 10.10.10.1/29
set services l3vpn Disneyland "Mickey Mouse" 1 device iosxr-1 redistribution-protocol [ connected ] interface TenGigabitEthernet-iosxr 2/0 port-mode true ipv4-local-prefix 10.10.10.9/29
set services l3vpn Disneyland "Mickey Mouse" 1 device iosxr-2 redistribution-protocol [ connected ] interface GigabitEthernet-iosxr 2/1 port-mode false encapsulation dot1q vlan-id [ 100 ] ipv4-local-prefix 10.10.10.17/29
```

## Authors

* Darren Bono - [darren.bono@att.net](mailto://darren.bono@att.net)
