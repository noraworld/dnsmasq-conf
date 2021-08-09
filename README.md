# dnsmasq-conf
Dnsmasq config files.

## Setup
```shell
cd dnsmasq-conf
sudo rm /etc/dnsmasq.conf
sudo rm -r /etc/dnsmasq.d
sudo ln -s $PWD/dnsmasq/dnsmasq.conf /etc
sudo ln -s $PWD/dnsmasq/dnsmasq.d /etc
sudo mkdir /etc/dnsmasq.toggle
sudo systemctl enable dnsmasq
```
