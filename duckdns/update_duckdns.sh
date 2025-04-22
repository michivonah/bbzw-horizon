#!/bin/bash

IP=$(ip addr show wlan0 | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1)
curl -s 'https://www.duckdns.org/update?domains=<DOMAIN>&token=<TOKEN>&ip='$IP