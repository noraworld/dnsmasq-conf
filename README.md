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

## Find links not blocked by Dnsmasq

`bin/extract-unfiltered` reads a UTF-8 Markdown/text file and writes an HTML
list of links containing unblocked domains. Requires Python 3.7 or later;
no third-party packages are needed.

```shell
bin/extract-unfiltered links.md \
  --dnsmasq-dir="dnsmasq,~/Workspace/envsman/raspberrypi/dnsmasq/dnsmasq.priv" \
  --out="reports/unfiltered.html"
```

- `--dnsmasq-dir` is required. All `.conf` files in the comma-separated
  directories are read recursively, including directories reached through
  symbolic links. Relative paths use the current working directory; absolute
  paths and `~` are also supported.
- Only `address` rules with an empty address, an unspecified IP (`0.0.0.0`,
  `::`), or a loopback IP are treated as blocks. Multiple domains in a rule,
  subdomains, and Unicode/punycode equivalents are supported. Everything after
  `#`, `server` rules, catch-all rules, and ordinary IP mappings are ignored.
  This checks the supplied configuration files, not live DNS or which
  configuration files the running daemon has enabled.
- URLs with a scheme and `://` are extracted throughout each line, including
  Markdown titles and multiple URLs per line. URLs in a nested link title use
  the outer link's destination. Separate links on one line keep their own
  destinations. A URL outside Markdown links uses the line's sole link when
  present; otherwise it uses its own URL and the line as its title.
- Each containing link produces at most one row per displayed domain per line.
  The display omits a leading `www.`; matching still uses the full hostname.
  Titles are preserved as text and all HTML values are escaped.
- `--out` defaults to `./unfiltered.html`. A path without a filename extension
  is treated as a directory and receives `unfiltered.html`. Missing parent
  directories are created automatically.

Run the regression tests with:

```shell
python3 -m unittest discover -s tests
```
