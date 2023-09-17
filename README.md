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

# Do not create a symbolic link because systemd-resolved causes "Failed to open /etc/hosts: Permission denied." Use a hard link instead as shown below.
sudo ln $PWD/etc/hosts /etc

sudo systemctl enable dnsmasq
```

## How to check syntax
```
dnsmasq --test
```
