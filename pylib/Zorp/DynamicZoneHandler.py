from Zone import Zone
from Subnet import Subnet
import Common
import kzorp.messages
import kzorp.netlink
import kzorp.communication
import socket
import prctl
import itertools

class DynamicZoneHandler(object):
    def __init__(self, zones, dnscache):
        self.zones = zones
        self.dnscache = dnscache

    def setup_dns_cache(self):
        """
        Fills up the DNS cache with host found in zones.py
        """

        for zone in self.zones:
            for hostname in zone.hostnames:
                try:
                    self.dnscache.addHost(hostname)
                    ttl = self.dnscache.lookupTTL(hostname)
                    dnsaddresses = self.dnscache.lookupHostname(hostname)
                    Common.log(None, Common.CORE_DEBUG, 6,
                               "Hostname initially added to the cache; name='%s', ttl='%d', addresses='%s', zone='%s'" %
                               (hostname, ttl, dnsaddresses, zone.name))
                except KeyError:
                    Common.log(None, Common.CORE_ERROR, 2,
                               "Hostname cannot be resolved; name='%s', zone='%s'" %
                               (hostname, zone.name))

    def _create_add_zone_messages_from_zone(self, zone, num_of_hostname_subnets = 0):
        subnet_num = len(zone.subnets) + num_of_hostname_subnets
        pname = zone.admin_parent.name if zone.admin_parent else None
        return kzorp.messages.KZorpAddZoneMessage(zone.name, pname, subnet_num = subnet_num)

    def _create_add_zone_subnet_messages_from_zone(self, zone):
        add_zone_subnet_messages = []
        for subnet in zone.subnets:
            add_zone_subnet_message = kzorp.messages.KZorpAddZoneSubnetMessage(zone.name,
                                                                     subnet.get_family(),
                                                                     subnet.addr_packed(),
                                                                     subnet.netmask_packed())
            add_zone_subnet_messages.append(add_zone_subnet_message)
        return add_zone_subnet_messages

    def create_zone_static_address_initialization_messages(self):
        add_zone_messages = []
        add_zone_subnet_messages = []
        for zone in sorted(self.zones, cmp=lambda z1, z2: cmp(z1.getDepth(), z2.getDepth())):
            add_zone_messages += [self._create_add_zone_messages_from_zone(zone), ]
            add_zone_subnet_messages += self._create_add_zone_subnet_messages_from_zone(zone)
        return add_zone_messages + add_zone_subnet_messages

    def _create_hostname_address_to_zone_map(self, updatable_zone):
        hostname_address_to_zone_map = {}
        for (zone_name, zone) in Zone.zones.iteritems():
            if zone_name == updatable_zone.name:
                continue

            for hostname in zone.hostnames:
                try:
                    ipv4_addresses, ipv6_addresses = self.dnscache.lookupHostname(hostname)
                except KeyError:
                    ipv4_addresses, ipv6_addresses = (set(), set())
                for address in ipv4_addresses | ipv6_addresses:
                    hostname_address_to_zone_map[address] = zone
        return hostname_address_to_zone_map

    @staticmethod
    def _create_conflicting_zone_to_address_map(add_zone_subnet_messages_for_dynamic_addresses,
                                                hostname_address_to_zone_map, updatable_zone):
        conflicting_zone_addresses_map = {}
        for msg in add_zone_subnet_messages_for_dynamic_addresses:
            address = socket.inet_ntop(msg.family, msg.address)
            zone = hostname_address_to_zone_map.get(address, None)
            if zone is not None and zone.name != updatable_zone.name:
                conflicting_zone_addresses_map[zone] = conflicting_zone_addresses_map.get(zone, []) + [address, ]
        return conflicting_zone_addresses_map

    def create_zone_update_messages(self, expired_hostname):
        updatable_zone = Zone.lookupByHostname(expired_hostname)

        if updatable_zone is None:
            return []

        delete_zone_messages = [kzorp.messages.KZorpDeleteZoneMessage(updatable_zone.name), ]
        add_zone_subnet_messages_for_static_addresses = self._create_add_zone_subnet_messages_from_zone(updatable_zone)
        add_zone_subnet_messages_for_dynamic_addresses = self._create_add_zone_subnet_messages_of_hostnames(
            updatable_zone)

        hostname_address_to_zone_map = self._create_hostname_address_to_zone_map(updatable_zone)
        conflicting_zone_addresses_map = self._create_conflicting_zone_to_address_map(
            add_zone_subnet_messages_for_dynamic_addresses, hostname_address_to_zone_map, updatable_zone)

        add_zone_subnet_messages_for_dynamic_addresses = filter(
            lambda msg: socket.inet_ntop(msg.family, msg.address) not in conflicting_zone_addresses_map,
            add_zone_subnet_messages_for_dynamic_addresses)
        for (conflicting_zone, conflicting_addresses) in conflicting_zone_addresses_map.iteritems():
            delete_zone_messages += [kzorp.messages.KZorpDeleteZoneMessage(conflicting_zone.name), ]
            add_zone_subnet_messages_for_static_addresses += self._create_add_zone_subnet_messages_from_zone(
                conflicting_zone)
            add_zone_subnet_messages = self._create_add_zone_subnet_messages_of_hostnames(conflicting_zone)
            add_zone_subnet_messages_for_dynamic_addresses = \
                filter(lambda msg: socket.inet_ntop(msg.family, msg.address) not in conflicting_addresses,
                       add_zone_subnet_messages_for_dynamic_addresses) + \
                filter(lambda msg: socket.inet_ntop(msg.family, msg.address) not in conflicting_addresses,
                       add_zone_subnet_messages)

        zone_names = set([ msg.name for msg in delete_zone_messages ])
        add_zone_messages = []
        for zone_name in zone_names:
            subnet_num = len(filter(lambda msg: msg.zone_name == zone_name,
                                    add_zone_subnet_messages_for_static_addresses + \
                                    add_zone_subnet_messages_for_dynamic_addresses))
            zone = Zone.lookupByName(zone_name)
            parent_name = zone.admin_parent.name if zone.admin_parent is not None else None
            add_zone_messages += [ kzorp.messages.KZorpAddZoneMessage(zone.name, parent_name, subnet_num), ]

        return delete_zone_messages + add_zone_messages + \
            add_zone_subnet_messages_for_static_addresses + \
            add_zone_subnet_messages_for_dynamic_addresses

    def update_zone(self, hostname):
        pass

    @staticmethod
    def __create_add_zone_subnet_messages(zone, ipv4_addresses, ipv6_addresses):
        add_zone_subnet_messages = []

        for address in ipv4_addresses:
            add_zone_subnet_message = kzorp.messages.KZorpAddZoneSubnetMessage(zone.name, socket.AF_INET,
                                                                     socket.inet_pton(socket.AF_INET, address))
            add_zone_subnet_messages.append(add_zone_subnet_message)
        for address in ipv6_addresses:
            add_zone_subnet_message = kzorp.messages.KZorpAddZoneSubnetMessage(zone.name, socket.AF_INET6,
                                                                     socket.inet_pton(socket.AF_INET6, address))
            add_zone_subnet_messages.append(add_zone_subnet_message)

        return add_zone_subnet_messages

    def _create_add_zone_subnet_messages_of_hostnames(self, zone):
        def has_zone_with_static_address(address):
            subnet = Subnet.create(address)
            zone = Zone.lookupByStaticAddressExactly(subnet)
            return zone is not None

        add_zone_subnet_messages = []
        for hostname in zone.hostnames:
            try:
                ipv4_addresses, ipv6_addresses = self.dnscache.lookupHostname(hostname)

                non_conflicting_ipv4_addresses = filter(
                    lambda ipv4_address: not has_zone_with_static_address(ipv4_address),
                    ipv4_addresses)
                non_conflicting_ipv6_addresses = filter(
                    lambda ipv6_address: not has_zone_with_static_address(ipv6_address),
                    ipv6_addresses)

                add_zone_subnet_messages += self.__create_add_zone_subnet_messages(zone, non_conflicting_ipv4_addresses,
                                                                                   non_conflicting_ipv6_addresses)
            except KeyError:
                pass
        return add_zone_subnet_messages

    def create_zone_dynamic_address_initialization_messages(self):
        def get_zone_name_from_message(msg):
            attr_name_by_command = {
                                     kzorp.messages.KZNL_MSG_ADD_ZONE:        'name',
                                     kzorp.messages.KZNL_MSG_DELETE_ZONE:     'name',
                                     kzorp.messages.KZNL_MSG_ADD_ZONE_SUBNET: 'zone_name',
                                   }
            return getattr(msg, attr_name_by_command[msg.command])

        messages = {}
        for zone in self.zones:
            for hostname in zone.hostnames:
                update_messages = self.create_zone_update_messages(hostname)
                updatable_zone_names = set([get_zone_name_from_message(msg) for msg in update_messages])
                for updatable_zone_name in updatable_zone_names:
                    zone_related_messages = filter(
                                            lambda msg: get_zone_name_from_message(msg) == updatable_zone_name,
                                            update_messages)
                    messages[updatable_zone_name] = zone_related_messages
        return itertools.chain(*messages.values())

    def setup(self):
        with ZoneDownload() as zone_download:
            messages = self.create_zone_static_address_initialization_messages()
            zone_download.initial(messages)
        self.setup_dns_cache()
        with ZoneDownload() as zone_download:
            messages = self.create_zone_dynamic_address_initialization_messages()
            zone_download.update(messages)

class ZoneDownload(object):
    def __init__(self):
        self.kzorp_handle = kzorp.communication.Handle()

    def __enter__(self):
        self.__acquire_caps()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.__drop_caps()

    def __acquire_caps(self):
        """ aquire the CAP_NET_ADMIN capability """

        try:
            prctl.set_caps((prctl.CAP_NET_ADMIN, prctl.CAP_EFFECTIVE, True))
        except OSError, e:
            Common.log(None, Common.CORE_ERROR, 1, "Unable to acquire NET_ADMIN capability; error='%s'" % (e))
            raise e

    def __drop_caps(self):
        """ drop the CAP_NET_ADMIN capability """

        try:
            prctl.set_caps((prctl.CAP_NET_ADMIN, prctl.CAP_EFFECTIVE, False))
        except OSError, e:
            Common.log(None, Common.CORE_ERROR, 1, "Unable to drop NET_ADMIN capability; error='%s'" % (e))
            raise e

    def __send_messages(self, messages):
        try:
            kzorp.communication.startTransaction(self.kzorp_handle, kzorp.messages.KZ_INSTANCE_GLOBAL)

            for message in messages:
                self.kzorp_handle.exchange(message)

            kzorp.communication.commitTransaction(self.kzorp_handle)
        except kzorp.netlink.NetlinkException as e:
            Common.log(None, Common.CORE_ERROR, 6,
                       "Error occured while downloading zones to kernel; error='%s'" % (e.detail))
            raise e

    def initial(self, messages):
        self.__send_messages([kzorp.messages.KZorpFlushZonesMessage(), ] + messages)

    def update(self, messages):
        self.__send_messages(messages)
