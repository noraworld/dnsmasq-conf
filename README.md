# dnsmasq-conf
Dnsmasq config files.

## Setup
### Step 1
Execute the following commands.

```shell
cd dnsmasq-conf
sudo rm /etc/dnsmasq.conf
sudo rm -r /etc/dnsmasq.d
sudo ln -s $PWD/dnsmasq/dnsmasq.conf /etc
sudo ln -s $PWD/dnsmasq/dnsmasq.d    /etc
sudo ln -s $PWD/dnsmasq/dnsmasq.priv /etc
sudo mkdir /etc/dnsmasq.toggle
sudo systemctl enable dnsmasq
```

### Step 2
Create a new file as `dnsmasq/dnsmasq.priv/dnsv6.conf`, and write the following in it.

```
dhcp-option=option6:dns-server,[xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx]
```

`xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx` is your IPv6 global unicast address assigned at your computer.

## How to check syntax
```
dnsmasq --test
```
