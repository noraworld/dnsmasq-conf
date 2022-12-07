# dnsmasq-conf
Dnsmasq config files.

## Setup
### Step 1
Execute the following commands.

```shell
cd dnsmasq-conf
ln -s <YOUR_PRIVATE_DNSMASQ_CONF_DIR> $PWD/dnsmasq/dnsmasq.priv

sudo rm /etc/dnsmasq.conf
sudo rm -r /etc/dnsmasq.d

sudo mkdir    /etc/dnsmasq.toggle
sudo mkdir -p /etc/dnsmasq.priv/toggle

sudo ln -s $PWD/dnsmasq/dnsmasq.conf  /etc
sudo ln -s $PWD/dnsmasq/dnsmasq.d     /etc
sudo ln -s $PWD/dnsmasq/dnsmasq.blist /etc
sudo ln -s $PWD/dnsmasq/dnsmasq.wlist /etc

sudo ln -s $PWD/dnsmasq/dnsmasq.priv/default   /etc/dnsmasq.priv
sudo ln -s $PWD/dnsmasq/dnsmasq.priv/blist /etc/dnsmasq.priv
sudo ln -s $PWD/dnsmasq/dnsmasq.priv/wlist /etc/dnsmasq.priv

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
