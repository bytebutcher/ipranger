# vim: ts=8:sts=8:sw=8:noexpandtab
#
# This file is part of ipranger.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import unittest

from parameterized import parameterized

from ipranger.ipranger import IPRangerGenerator, IPAddresses, IPAddress, Part, Range


class TestIPRangerFormatParser(unittest.TestCase):

    def test_single_ip_address(self):
        input = IPAddresses([IPAddress(Part(octets=[0]), Part(octets=[0]), Part(octets=[0]), Part(octets=[0]))])
        self.assertEqual(list(IPRangerGenerator().generate([input])), ["0.0.0.0"])

    def test_single_ip_address_range(self):
        input = IPAddresses([IPAddress(Part(ranges=[Range(0, 1)]), Part(octets=[0]), Part(octets=[0]), Part(octets=[0]))])
        self.assertEqual(list(IPRangerGenerator().generate([input])), ["0.0.0.0", "1.0.0.0"])

    def test_single_ip_address_multi_range(self):
        input = IPAddresses(
            [IPAddress(Part(ranges=[Range(0, 1)]), Part(octets=[0]), Part(octets=[0]), Part(ranges=[Range(0, 1)]))]
        )
        self.assertEqual(list(IPRangerGenerator().generate([input])), ["0.0.0.0", "0.0.0.1", "1.0.0.0", "1.0.0.1"])

    @parameterized.expand([
        (32, 1),  # does only contain the single address
        (24, 254),  # does not contain network- and broadcast-address
        (26, 63),  # does not contain network-address
        (23, 254),
        (22, 3 * 254),
    ])
    def test_single_ip_address_cidr(self, cidr, number_of_values):
        input = IPAddresses([IPAddress(Part(octets=[1]), Part(octets=[1]), Part(octets=[1]), Part(octets=[1]), cidr=cidr)])
        self.assertEqual(len(list(IPRangerGenerator().generate([input]))), number_of_values)

    def test_multiple_ip_addresses(self):
        input = IPAddresses([
            IPAddress(Part(octets=[0]), Part(octets=[0]), Part(octets=[0]), Part(octets=[0])),
            IPAddress(Part(octets=[1]), Part(octets=[1]), Part(octets=[1]), Part(octets=[1]))
        ])
        self.assertEqual(list(IPRangerGenerator().generate([input])), ["0.0.0.0", "1.1.1.1"])
