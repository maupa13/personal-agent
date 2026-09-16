#!/bin/sh
# VPS1 only: scoped INPUT chain; never flush or replace existing rules.
set -eu
iptables -w -N VPS-EGRESS 2>/dev/null || iptables -w -S VPS-EGRESS >/dev/null
iptables -w -C VPS-EGRESS -i lo -j ACCEPT 2>/dev/null || iptables -w -A VPS-EGRESS -i lo -j ACCEPT
iptables -w -C VPS-EGRESS -s 172.30.0.10/32 -d 172.30.0.1/32 -i br-55968fb2080f -j ACCEPT 2>/dev/null || iptables -w -A VPS-EGRESS -s 172.30.0.10/32 -d 172.30.0.1/32 -i br-55968fb2080f -j ACCEPT
iptables -w -C VPS-EGRESS -j REJECT 2>/dev/null || iptables -w -A VPS-EGRESS -j REJECT
iptables -w -C INPUT -p tcp --dport 18981 -j VPS-EGRESS 2>/dev/null || iptables -w -I INPUT 1 -p tcp --dport 18981 -j VPS-EGRESS
ip -4 addr show | grep -q '172.30.0.1/24'
