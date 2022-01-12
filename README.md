# ipranger

![GitHub](https://img.shields.io/github/license/bytebutcher/ipranger)
![PyPI](https://img.shields.io/pypi/v/ipranger)

![ipranger Logo](https://raw.githubusercontent.com/bytebutcher/ipranger/master/ipranger/images/ipranger.png)

A python package and commandline tool for generating IPv4-addresses based on schema.

## Setup

```ipranger``` can be installed either by using ```pip``` or by pulling the source from this repository:
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
from ipranger import ip_addresses_type
parser = argparse.ArgumentParser(description='Scan IPv4 addresses')
parser.add_argument('IP_ADDRESSES', type=ip_addresses_type,
                    help="List of IPv4 addresses e.g. '192.168.0.1' '192.168.0.1,3-20', '192.168.0.1/24'")
arguments = parser.parse_args()
print(arguments.ip_addresses)
```

Another way to interact with ```ipranger``` in python programs is by importing the ```generate``` method:
```
from ipranger import generate
print(generate(include_list=set('192.168.0.1-6'), exclude_list=set('192.168.0.2'))
```
