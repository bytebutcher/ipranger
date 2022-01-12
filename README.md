# ipranger

![ipranger Logo](https://github.com/bytebutcher/ipranger/raw/main/images/ipranger.png)

A python package and commandline tool for generating IPv4-addresses based on a schema.

## Setup

```ipranger``` can be installed either by using ```pip``` or by pulling the source code from this repository:
```bash
# Install using pip
pip3 install ipranger
```

## Overview

This section provides an overview of the individual ways to interact with ```ipranger```.

### Command Line

```ipranger``` can be directly used via the commandline and as such included in bash-scripts for advanced IPv4 address
format processing.

```
# Print IPv4 subnet
$ ipranger 192.0.0.1/29
192.0.2.1
192.0.2.2
...
192.0.2.6

# Ranges, comma separated values and IPv4 addresses
$ ipranger 192.168.2.1,2,192.168.2.3,4,5-6
192.0.2.1
192.0.2.2
...
192.0.2.6

# Exclude IPv4 addresses
$ ipranger 192.168.2.1-6 --exclude 192.168.2.2
192.0.2.1
192.0.2.3
...
192.0.2.6
```

### Package

```ipranger``` can be used via the custom argparse type ```ip_addresses_type```:
```
import argparse
from ipranger.ipranger import ip_addresses_type
parser = argparse.ArgumentParser(description='Scan IPv4 addresses')
parser.add_argument('ip_addresses', type=ip_addresses_type,
                    help="List of IPv4 addresses e.g. '192.168.0.1' '192.168.0.1,3-20', '192.168.0.1/24'")
arguments = parser.parse_args()
for ip_address in arguments.ip_addresses:
    print(ip_address)
```

Another way to interact with ```ipranger``` in python programs is by importing the ```generate``` method:
```
from ipranger.ipranger import generate
for ip_address in generate(include_list=['192.168.0.1-6'], exclude_list=['192.168.0.2']):
    print(ip_address)
```
