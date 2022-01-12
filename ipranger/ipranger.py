#!/usr/bin/env python3
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
import argparse
import logging
import sys
import traceback
from dataclasses import dataclass
import dacite
import pyparsing as pp
from typing import List, Set, Iterator


class Logger:

    def __init__(self, app_id, log_format, level):
        self._logger = logging.getLogger(app_id)
        self._handler = logging.StreamHandler(sys.stderr)
        self._handler.setFormatter(logging.Formatter(log_format))
        self._logger.addHandler(self._handler)
        self._set_level(level)

    def _set_level(self, level):
        self._logger.setLevel(level)
        self._handler.setLevel(level)

    def _get_level(self):
        return self._logger.level

    def info(self, msg):
        self._logger.info(" INFO: {msg}".format(msg=msg))

    def debug(self, msg):
        self._logger.debug("DEBUG: {msg}".format(msg=msg))

    def warning(self, msg):
        self._logger.warning(" WARN: {msg}".format(msg=msg))

    def error(self, msg):
        self._logger.info("ERROR: {msg}".format(msg=msg))

    level = property(fset=_set_level, fget=_get_level)


@dataclass
class Range:
    start: int
    end: int


@dataclass
class Part:
    octets: List[int] = None
    ranges: List[Range] = None


@dataclass
class IPAddress:
    p1: Part
    p2: Part
    p3: Part
    p4: Part
    cidr: int = None


@dataclass
class IPAddresses:
    addresses: List[IPAddress]


def make_int_range_condition(minval, maxval):
    in_range = lambda x, minval=minval, maxval=maxval: minval <= x <= maxval
    return lambda t: in_range(t[0])


def make_range_condition():
    in_range = lambda x: x['start'] < x['end']
    return lambda t: in_range(t[0])


class IPRangerFormatParser:
    """
    Parses an IPRanger format into a list of IP-addresses.

    IPRanger format examples:

        # Single IP-Address
        192.168.0.1

        # Multiple comma-separated IP-Addresses
        192.168.0.1,192.168.0.2

        # IP-Address with comma-separated values
        192.168.0.1,2

        # IP-Address with range
        192.168.0.1-2

        # IP-Address with CIDR notation
        192.168.0.1/24

        # Multiple comma-separated IP-Addresses with comma-separated values, ranges and CIDR notation
        192.168.0,1.1,4,5-6,192.168.2.1/24
    """

    IP_ADDRESSES = pp.Forward()

    # A set of tokens
    DOT, COMMA, DASH, SLASH = map(pp.Suppress, ".,-/")

    # A number between 0 and 255
    OCTET = pp.Word(pp.nums, min=1, max=3) \
        .setParseAction(lambda toks: int(toks[0])) \
        .addCondition(make_int_range_condition(0, 255)) \
        .setResultsName("octets*")

    # Range-specification (e.g. "1-10", "0-255", etc.)
    RANGE = pp.Combine(OCTET().setResultsName("start") + DASH + OCTET().setResultsName("end")) \
        .addCondition(make_range_condition()) \
        .setResultsName("ranges*")

    ITEM = pp.Or(RANGE | OCTET)

    # Each part of an ip-address may contain comma-separated values and ranges.
    PART = pp.Group(ITEM + pp.ZeroOrMore(COMMA + ITEM))
    PART_1 = PART.setResultsName('p1')
    PART_2 = PART.setResultsName('p2')
    PART_3 = PART.setResultsName('p3')
    PART_4 = PART.setResultsName('p4')

    # Classless Inter-Domain Routing Notation (e.g. '/1,' '/2', ..., '/32')
    CIDR = SLASH + pp.Word(pp.nums, min=1, max=2) \
        .setParseAction(lambda toks: int(toks[0])) \
        .addCondition(make_int_range_condition(1, 32)) \
        .setResultsName("cidr")

    #
    IP_ADDRESSES << pp.Or(
        pp.Group(
            PART_1 + DOT + PART_2 + DOT + PART_3 + DOT + PART_4 + CIDR
        ).setResultsName("addresses*") + COMMA + IP_ADDRESSES |
        pp.Group(
            PART_1 + DOT + PART_2 + DOT + PART_3 + DOT + pp.Combine(pp.OneOrMore(ITEM + COMMA)).setResultsName("p4")
        ).setResultsName("addresses*") + IP_ADDRESSES |
        pp.Group(
            PART_1 + DOT + PART_2 + DOT + PART_3 + DOT + PART_4 + CIDR
        ).setResultsName("addresses*") |
        pp.Group(
            PART_1 + DOT + PART_2 + DOT + PART_3 + DOT + PART_4
        ).setResultsName("addresses*")
    )

    def parse(self, ip_addresses: str) -> IPAddresses:
        try:
            # Parse IP addresses and transform them into IPAddresses object.
            return dacite.from_dict(IPAddresses, self.IP_ADDRESSES.parse_string(ip_addresses, parse_all=True).as_dict())
        except Exception:
            raise Exception("Failed to resolve \"{format}\".".format(format=ip_addresses))


class IPRangerGenerator:
    """
    The IPRangerGenerator transforms the result of the IPRangerFormatParser into a list of IP-addresses.
    """

    def _expand_cidr(self, parts, cidr=None) -> [Set[int], Set[int], Set[int], Set[int]]:
        """ Expands a CIDR by adding the matching octets to the list of parts. """
        if not cidr:
            # if no cidr was defined, we return the parts untouched
            return parts

        # Initialize mask with cidr remainder
        mask = 8 - (cidr % 8)
        for index in range(int(cidr / 8), 4):
            if index == 0:
                # IP address should not start with 0 but may contain 255.
                parts[index].update(range(1, int('1' * mask, 2) + 1))
            elif index == 3:
                if mask == 8:
                    # IP address should not end with 0 or 255.
                    parts[index].update(range(1, int('1' * mask, 2)))
                else:
                    # IP address should not end with 0.
                    parts[index].update(range(1, int('1' * mask, 2) + 1))
            else:
                # 2nd and 3rd part of IP address may contain 0 and 255.
                parts[index].update(range(1, int('1' * mask, 2) + 1))
            # After first run, mask full byte
            mask = 8

        return parts

    def _resolve_part(self, part: Part) -> Set[int]:
        """ Resolves a list of octets and ranges into a set of octets. """
        result = set()
        if part.octets:
            result.update(part.octets)
        if part.ranges:
            for _range in part.ranges:
                result.update(range(_range.start, _range.end + 1))
        return result

    def _resolve_ip_address(self, ip_address: IPAddress) -> [Set[int], Set[int], Set[int], Set[int]]:
        """ Resolves the result of the IPRangerFormatParser into a list of parts. """
        cidr = None
        if ip_address.cidr:
            cidr = ip_address.cidr
        return self._expand_cidr([
            self._resolve_part(ip_address.p1),
            self._resolve_part(ip_address.p2),
            self._resolve_part(ip_address.p3),
            self._resolve_part(ip_address.p4)
        ], cidr)

    def _resolve_ip_addresses(
            self, ip_addresses_list: List[IPAddresses] = None) -> List:
        """
        Resolves a list of IPRangerFormatParser results into a list of lists of parts.
        :param ip_addresses_list: list of parsed IP-addresses.
        :return: list of lists of parts.
        """
        result = []
        if ip_addresses_list:
            for target in ip_addresses_list:
                for ip_address in target.addresses:
                    result.append(self._resolve_ip_address(ip_address))
        return result

    def _should_exclude_ip_address(self, p1: int, p2: int, p3: int, p4: int,
                                   resolved_excluded_ip_addresses: List[List[int]]) -> bool:
        """
        Returns whether the IP-address should be excluded.
        :return: True, when IP-address should be excluded, otherwise False.
        """
        for ep1, ep2, ep3, ep4 in resolved_excluded_ip_addresses:
            if p1 in ep1 and p2 in ep2 and p3 in ep3 and p4 in ep4:
                return True
        return False

    def generate(self, include_list: List[IPAddresses], exclude_list: List[IPAddresses] = None) -> Iterator[str]:
        """
        Generates list of IP-addresses based on list of IP-addresses to include and list of IP-addresses to exclude.
        :param include_list: list of IP-addresses to include.
        :param exclude_list: list of IP-addresses to exclude.
        :return: list of IP-addresses (e.g. '1.1.1.1', '1.2.1.1', '1.3.1.1', '1.4.1.1', '1.5.1.1', ...)
        """
        resolved_excluded_ip_addresses = self._resolve_ip_addresses(exclude_list)
        for part_1, part_2, part_3, part_4 in self._resolve_ip_addresses(include_list):
            for p1 in part_1:
                for p2 in part_2:
                    for p3 in part_3:
                        for p4 in part_4:
                            if self._should_exclude_ip_address(p1, p2, p3, p4, resolved_excluded_ip_addresses):
                                continue
                            yield '{}.{}.{}.{}'.format(p1, p2, p3, p4)


class IPRanger:

    def generate(self, include_list: List[str], exclude_list: List[str]) -> Iterator[str]:
        """
        Generates list of IP-addresses based on list of IP-addresses to include and list of IP-addresses to exclude.
        IP-addresses need to conform to the IPRanger IP-address specification.
        :param include_list: list of IP-addresses to include.
        :param exclude_list: list of IP-addresses to exclude.
        :return: list of IP-addresses (e.g. '1.1.1.1', '1.2.1.1', '1.3.1.1', '1.4.1.1', '1.5.1.1', ...)
        """
        parsed_include_list = [
            IPRangerFormatParser().parse(included_target) for included_target in include_list
        ]
        parsed_exclude_list = [
            IPRangerFormatParser().parse(excluded_target) for excluded_target in exclude_list
        ]
        for ip_address in IPRangerGenerator().generate(parsed_include_list, parsed_exclude_list):
            yield ip_address


def generate(include_list: List[str], exclude_list: List[str] = None) -> Iterator[str]:
    """
    Shorthand function which can be included by other packages to generate IP addresses from a set of IP addresses
    in the ipranger format.
    """
    if not exclude_list:
        exclude_list = []
    return IPRanger().generate(include_list, exclude_list)


def ip_addresses_type(ipranger_format: str) -> Iterator[str]:
    """Custom argparse type for IP addresses in the ipranger format given from the command line"""
    try:
        return generate([ipranger_format])
    except Exception as err:
        raise argparse.ArgumentTypeError(err)


def main():
    # Initialize logger
    log_level = logging.DEBUG if "--debug" in sys.argv else logging.INFO
    logger = Logger("ipranger", "%(msg)s", log_level)
    try:
        # Initialize argument parser
        parser = argparse.ArgumentParser(description='ipranger')
        parser.add_argument('ip_addresses', action='store', metavar='ip_addresses',
                            nargs='?', help='Include host/networks')
        parser.add_argument('-iL', '--include-list', action='store', metavar='filename',
                            dest='include_list', type=argparse.FileType('r'),
                            help='Include list of hosts/networks')
        parser.add_argument('-eL', '--exclude-list', action='store', metavar='filename',
                            dest='exclude_list', type=argparse.FileType('r'),
                            help='Exclude list of hosts/networks')
        parser.add_argument('--exclude', metavar='ip_addresses',
                            dest='exclude',
                            help='Exclude hosts/networks')
        parser.add_argument('--debug', action='store_true',
                            dest='debug',
                            help='Additional debug information (e.g. stack traces)')

        # Parse all arguments
        arguments = parser.parse_args()

        # Collect all targets to include
        include_list = set()
        if arguments.ip_addresses:
            include_list.update([arguments.ip_addresses])
        if arguments.include_list:
            include_list.update(arguments.include_list.readlines())
        if not include_list:
            raise Exception('No targets were specified!')

        # Collect all targets to exclude
        exclude_list = set()
        if arguments.exclude:
            exclude_list.update([arguments.exclude])
        if arguments.exclude_list:
            exclude_list.update(arguments.exclude_list.readlines())

        # Generate and print targets
        for target in IPRanger().generate(list(include_list), list(exclude_list)):
            print(target)
    except Exception as err:
        # Print exception message to the screen. Note that these are (if there is no programming error) controlled
        # exceptions and contain only messages which are actually useful for the user.
        logger.error(str(err))
        if log_level == logging.DEBUG:
            traceback.print_exc()
        sys.exit(1)
    except KeyboardInterrupt:
        # Catch keyboard interrupt usually caused when user presses CTRL+C and exit program without showing the
        # cryptic exception.
        logger.debug("Interrupted program (presumably via CTRL+C) ...")
        logger.debug("Aborting ...")
        sys.exit(1)


if __name__ == '__main__':
    main()
