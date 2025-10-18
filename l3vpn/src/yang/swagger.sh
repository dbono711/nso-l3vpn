yanger -p . -t expand -f swagger \
  --swagger-path-filter=/data/tailf-ncs-services:services/l3vpn:l3vpn \
  --swagger-host 127.0.0.1:8080 \
  --swagger-basepath /restconf \
  l3vpn.yang
