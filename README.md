# nso-l3vpn

Cisco NSO service package for orchestrating MPLS Layer 3 VPN (L3VPN) services on Cisco IOS and IOS-XR devices

***_NOTE:_ Not all features for implementating MPLS L3VPN's are implemented. Rather, this package provides a common approach to Service Provider (SP) related configuration required for supporting MPLS L3VPN's for customers**

## Overview

A Multiprotocol Label Switching (MPLS) Layer 3 Virtual Private Network (L3VPN) consists of a set of sites that are interconnected by means of an MPLS provider core network. At each customer site, one or more customer edge (CE) routers attach to one or more provider edge (PE) routers. This NSO service package provides the orchestration for MPLS L3VPN’s between Cisco IOS/IOS-XR Provider Edge (PE) networking devices.

## Features

1. Support's the selection of a ```customer-name``` as a unique identifier for a service instance
2. Support's the manual entry of a ```service-id``` as a unique identifier for a service instance
3. Support's the manual entry of a Virtual Private Network (VPN) identifier at the service level
    1. The ```vpn-id``` is used in automatically generating Route-Target (RT) and Route-Distinguisher (RD) values
4. Support's the ability to set the maximum number of routes accepted by the L3VPN at the service level (range: 1..5000, default: 100)
    1. Support's the ability to set the warning percentage for the maximum routes (range: 1..100, default: 80)
5. Support's the manual entry of the Provider Edge (PE) ASN at the service level
    1. The ```asn``` is used in automatically generating Route-Target (RT) and Route-Distinguisher (RD) values
6. Support's the ability to specify the use of IPv4, IPv6, or both at the service level
7. Each service MUST consist of two (2) or more Provider Edge (PE)
    1. Support's Cisco IOS and Cisco IOS-XR Operating Systems
        1. VRF names adhere to Cisco IOS-XR special character and length (1..32 characters) limitations
        2. Route-Distinguishers (RD’s) adhere to [Type 1 encoding](https://datatracker.ietf.org/doc/rfc4364/)
    2. Support's one (1) or more User-Network-Interfaces (UNI) on each Provider Edge (PE) device
        1. Provides the user with an existing list of interfaces on the PE device for selection
        2. Support's Static Routing as the Provider Edge (PE) to Customer Edge (CE) routing protocol
            1. Support's multiple forwarding addresses for the same static route
            2. Support's validation that the forwarding address of each static route falls within one of the device interfaces ipv4-prefix or ipv6-prefix
        3. Support's Border Gateway Protocol (BGP) as the Provider Edge (PE) to Customer Edge (CE) routing protocol
            1. Support's re-distribution of ```connected``` and/or ```static``` routes

## Assumptions

* The Provider (P) core has already been configured to provide MPLS transport
* The Provider Edge (PE) devices have already been configured to support MPLS L3VPN's

## Installation

Copy the [l3vpn](l3vpn) directory to your NSO runtime ```packages``` directory, and reload

For example:

```shell
cp -R l3vpn ~/nso/6.0-run/packages
ncs_cli -u admin
request packages reload
```

## Example Service Instance

```shell

# configure a customer to use since the model references the `/ncs:customers/ncs:customer` list
set customers customer Disneyland status active

# configure service
set services l3vpn Disneyland service01 vpn-id 1
set services l3vpn Disneyland service01 inet IPv4
set services l3vpn Disneyland service01 max-routes 100
set services l3vpn Disneyland service01 max-routes-warning 80
set services l3vpn Disneyland service01 provider-edge asn 65000
set services l3vpn Disneyland service01 provider-edge device iosxr-0 redistribute [ static connected ]
set services l3vpn Disneyland service01 provider-edge device iosxr-0 interface GigabitEthernet2/0 cir 80
set services l3vpn Disneyland service01 provider-edge device iosxr-0 interface GigabitEthernet2/0 mtu 2000
set services l3vpn Disneyland service01 provider-edge device iosxr-0 interface GigabitEthernet2/0 port-mode true
set services l3vpn Disneyland service01 provider-edge device iosxr-0 interface GigabitEthernet2/0 ipv4-local-prefix 172.16.1.0/31
set services l3vpn Disneyland service01 provider-edge device iosxr-0 ce-routing
set services l3vpn Disneyland service01 provider-edge device iosxr-0 ce-routing static
set services l3vpn Disneyland service01 provider-edge device iosxr-0 ce-routing static ipv4-destination-prefix 10.0.0.0/24 ipv4-forwarding [ 172.16.1.1 ]
set services l3vpn Disneyland service01 provider-edge device iosxr-1 interface GigabitEthernet2/0 cir 80
set services l3vpn Disneyland service01 provider-edge device iosxr-1 interface GigabitEthernet2/0 mtu 2000
set services l3vpn Disneyland service01 provider-edge device iosxr-1 interface GigabitEthernet2/0 port-mode true
set services l3vpn Disneyland service01 provider-edge device iosxr-1 interface GigabitEthernet2/0 ipv4-local-prefix 172.16.1.2/31
```
