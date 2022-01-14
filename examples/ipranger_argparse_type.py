import argparse
from ipranger.ipranger import ip_addresses_type
parser = argparse.ArgumentParser(description='Scan IPv4 addresses')
parser.add_argument('ip_addresses', type=ip_addresses_type,
                    help="List of IPv4 addresses e.g. '192.168.0.1' '192.168.0.1,3-20', '192.168.0.1/24'")
arguments = parser.parse_args()
for ip_address in arguments.ip_addresses:
    print(ip_address)

