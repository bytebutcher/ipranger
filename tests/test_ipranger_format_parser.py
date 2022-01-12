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
from ipranger.ipranger import IPRangerFormatParser, IPAddresses, IPAddress, Part, Range


class TestIPRangerFormatParser(unittest.TestCase):
    @parameterized.expand([
        ['1.2.3.4'],  # single ip address
        ['1,1.2.3.4'],  # - comma
        ['1-2.2.3.4'],  # - range
        ['1,1-2.2.3.4'],  # - range on the right
        ['1-2,1.2.3.4'],  # - range on the left
        ['1,1-2,1.2.3.4'],  # - range in the middle
        ['1-2,1,1-2,1.2.3.4'],  # - multiple ranges
        ['1.2.3.4/24'],  # - cidr

    ])
    def test_ip_addresses_valid(self, ip_address):
        try:
            IPRangerFormatParser().parse(ip_address)
        except:
            self.fail("IPRangerFormatParser.parse('{}') raised Exception unexpectedly!".format(ip_address))

    def test_single_ip_address(self):
        """ Testing whether single ip address can be parsed correctly. """
        expected = IPAddresses([IPAddress(Part(octets=[0]), Part(octets=[0]), Part(octets=[0]), Part(octets=[0]))])
        self.assertEqual(IPRangerFormatParser().parse('0.0.0.0'), expected)

    def test_single_ip_address_cidr(self):
        """ Testing whether single ip address with cidr notation can be parsed correctly. """
        expected = IPAddresses([IPAddress(Part(octets=[0]), Part(octets=[0]), Part(octets=[0]), Part(octets=[0]), cidr=24)])
        self.assertEqual(IPRangerFormatParser().parse('0.0.0.0/24'), expected)

    @parameterized.expand([
        [-1],
        [0],
        [33],
    ])
    def test_single_ip_address_cidr_invalid(self, cidr):
        with self.assertRaises(Exception):
            IPRangerFormatParser().parse('1.1.1.1/{cidr}'.format(cidr=cidr))

    def test_single_ip_address_comma_separated_octets(self):
        """ Testing whether single ip address with comma separated octets can be parsed correctly. """
        expected = IPAddresses([IPAddress(Part(octets=[0, 1, 2]), Part(octets=[0]), Part(octets=[0]), Part(octets=[0, 1, 2]))])
        self.assertEqual(IPRangerFormatParser().parse('0,1,2.0.0.0,1,2'), expected)

    def test_single_ip_address_ranges(self):
        """ Testing whether single ip address with range can be parsed correctly. """
        expected = IPAddresses([
            IPAddress(Part(ranges=[Range(1, 2)]), Part(octets=[0]), Part(octets=[0]), Part(ranges=[Range(1, 2)]))
        ])
        self.assertEqual(IPRangerFormatParser().parse('1-2.0.0.1-2'), expected)

    def test_single_ip_address_comma_separated_ranges(self):
        """ Testing whether single ip address with comma separated ranges can be parsed correctly. """
        expected = IPAddresses([
            IPAddress(
                Part(ranges=[Range(1, 2), Range(3, 4)]),
                Part(octets=[0]),
                Part(octets=[0]),
                Part(ranges=[Range(1, 2), Range(3, 4)])
            )
        ])
        self.assertEqual(IPRangerFormatParser().parse('1-2,3-4.0.0.1-2,3-4'), expected)

    def test_single_ip_address_comma_separated_ranges_and_octets(self):
        """ Testing whether single ip address with comma separated ranges can be parsed correctly. """
        expected = IPAddresses([
            IPAddress(
                Part(octets=[0], ranges=[Range(1, 2), Range(3, 4)]),
                Part(octets=[0]),
                Part(octets=[0]),
                Part(octets=[0], ranges=[Range(1, 2), Range(3, 4)])
            )
        ])
        self.assertEqual(IPRangerFormatParser().parse('0,1-2,3-4.0.0.0,1-2,3-4'), expected)

    @parameterized.expand([
        ['6.6.6.6.6.6'],  # too many parts
        ['5.5.5.5.5'],  # too many parts
        ['3.3.3'],  # too few parts
        ['2.2'],  # too few parts
        ['1']
    ])
    def test_single_ip_address_invalid_part_count(self, ip_address):
        """ Testing whether invalid numbers of parts raise an exception. """
        with self.assertRaises(Exception):
            IPRangerFormatParser().parse(ip_address)

    @parameterized.expand([
        ['A.A.A.A'],  # should be numeric
        ['256.256.256.256'],  # should be in the range of 0-255
    ])
    def test_single_ip_address_invalid_octet_value(self, ip_address):
        """ Testing whether invalid octet values raise an exception. """
        with self.assertRaises(Exception):
            IPRangerFormatParser().parse(ip_address)

    @parameterized.expand([
        ['1.2.3.4-'],
        ['1.2.3-.4'],
        ['1.2-.3.4'],
        ['1-.2.3.4'],
        ['-1.2.3.4'],
        ['1.-2.3.4'],
        ['1.2.-3.4'],
        ['1.2.3.-4'],
        ['1.2.3.4-5-'],
        ['1.2.3.-4-5'],
        ['1.2.3.-4-5-'],
        ['1.2.3.4--5'],
    ])
    def test_single_ip_address_invalid_range_specification(self, ip_address):
        """ Testing whether invalid range specification raises an exception. """
        with self.assertRaises(Exception):
            IPRangerFormatParser().parse(ip_address)


    @parameterized.expand([
        ['A-B.0.0.0'],  # octets should be integer
        ['1-1.0.0.0'],  # start should be less than end
        ['2-1.0.0.0'],  # start should be less than end
        ['256-257.0.0.0'],  # octets should be in the range of 0-255
    ])
    def test_single_ip_address_invalid_range_values(self, ip_address):
        """ Testing whether invalid octet values raise an exception. """
        with self.assertRaises(Exception):
            IPRangerFormatParser().parse(ip_address)

    def test_multiple_ip_addresses(self):
        """ Testing whether comma separated ip addresses can be parsed correctly. """
        expected = IPAddresses([
            IPAddress(Part(octets=[0]), Part(octets=[0]), Part(octets=[0]), Part(octets=[0])),
            IPAddress(Part(octets=[1]), Part(octets=[1]), Part(octets=[1]), Part(octets=[1]))
        ])
        self.assertEqual(IPRangerFormatParser().parse('0.0.0.0,1.1.1.1'), expected)

    def test_multiple_ip_addresses_with_cidr(self):
        """ Testing whether comma separated ip addresses with cidr can be parsed correctly. """
        expected = IPAddresses([
            IPAddress(Part(octets=[0]), Part(octets=[0]), Part(octets=[0]), Part(octets=[0]), cidr=24),
            IPAddress(Part(octets=[1]), Part(octets=[1]), Part(octets=[1]), Part(octets=[1]))
        ])
        self.assertEqual(IPRangerFormatParser().parse('0.0.0.0/24,1.1.1.1'), expected)
