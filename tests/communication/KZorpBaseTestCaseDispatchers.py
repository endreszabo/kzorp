
#
# Copyright (C) 2006-2012, BalaBit IT Ltd.
# This program/include file is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program/include file is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation,Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
from KZorpComm import KZorpComm
import socket
import testutil
import kzorp.kzorp_netlink as kznl
import types
import os
import errno

class KZorpBaseTestCaseDispatchers(KZorpComm):
    _dumped_dispatchers = []
    _zones = [
               #{'name' : 'a6', 'uname' :   'k6', 'pname' :   None, 'address' : 'fc00:0:101:1::', 'mask' : 64, 'family' : socket.AF_INET6},
               {'family' : socket.AF_INET, 'uname' : 'internet', 'subnets' : ['0.0.0.0/0'], 'admin_parent' : None},
               {'family' : socket.AF_INET, 'uname' : 'A',        'subnets' : ['10.99.101.0/25',   '10.99.201.0/25'], 'admin_parent' : None},
               {'family' : socket.AF_INET, 'uname' : 'AA',       'subnets' : ['10.99.101.0/28',   '10.99.201.0/28'],                  'admin_parent' : 'A'},
               {'family' : socket.AF_INET, 'uname' : 'AAA',      'subnets' : ['10.99.101.0/30',   '10.99.201.0/30'],                  'admin_parent' : 'AA'},
               {'family' : socket.AF_INET, 'uname' : 'AAZ',      'subnets' : ['10.99.101.4/30',   '10.99.201.4/30'],                 'admin_parent' : 'AA'},
               {'family' : socket.AF_INET, 'uname' : 'AB',       'subnets' : ['10.99.101.64/28',  '10.99.201.64/28'],                 'admin_parent' : 'A'},
               {'family' : socket.AF_INET, 'uname' : 'ABA',      'subnets' : ['10.99.101.64/30',  '10.99.201.64/30'],                  'admin_parent' : 'AB'},
               {'family' : socket.AF_INET, 'uname' : 'ABZ',      'subnets' : ['10.99.101.68/30',  '10.99.201.68/30'],                 'admin_parent' : 'AB'},
               {'family' : socket.AF_INET, 'uname' : 'AY',       'subnets' : ['10.99.101.80/28',  '10.99.201.80/28'],                 'admin_parent' : 'A'},
               {'family' : socket.AF_INET, 'uname' : 'AYA',      'subnets' : ['10.99.101.80/30',  '10.99.201.80/30'],                  'admin_parent' : 'AY'},
               {'family' : socket.AF_INET, 'uname' : 'AYZ',      'subnets' : ['10.99.101.84/30',  '10.99.201.84/30'],                 'admin_parent' : 'AY'},
               {'family' : socket.AF_INET, 'uname' : 'AZ',       'subnets' : ['10.99.101.16/28',  '10.99.201.16/28'],                 'admin_parent' : 'A'},
               {'family' : socket.AF_INET, 'uname' : 'AZA',      'subnets' : ['10.99.101.16/30',  '10.99.201.16/30'],                  'admin_parent' : 'AZ'},
               {'family' : socket.AF_INET, 'uname' : 'AZZ',      'subnets' : ['10.99.101.20/30',  '10.99.201.20/30'],                 'admin_parent' : 'AZ'},
               {'family' : socket.AF_INET, 'uname' : 'Z',        'subnets' : ['10.99.101.128/25', '10.99.201.128/25'], 'admin_parent' : None},
               {'family' : socket.AF_INET, 'uname' : 'ZA',       'subnets' : ['10.99.101.128/28', '10.99.201.128/28'],                  'admin_parent' : 'Z'},
               {'family' : socket.AF_INET, 'uname' : 'ZAA',      'subnets' : ['10.99.101.128/30', '10.99.201.128/30'],                  'admin_parent' : 'ZA'},
               {'family' : socket.AF_INET, 'uname' : 'ZAZ',      'subnets' : ['10.99.101.132/30', '10.99.201.132/30'],                 'admin_parent' : 'ZA'},
               {'family' : socket.AF_INET, 'uname' : 'ZB',       'subnets' : ['10.99.101.192/28', '10.99.201.192/28'],                    'admin_parent' : 'Z'},
               {'family' : socket.AF_INET, 'uname' : 'ZBA',      'subnets' : ['10.99.101.192/30', '10.99.201.192/30'],                  'admin_parent' : 'ZB'},
               {'family' : socket.AF_INET, 'uname' : 'ZBZ',      'subnets' : ['10.99.101.196/30', '10.99.201.196/30'],                 'admin_parent' : 'ZB'},
               {'family' : socket.AF_INET, 'uname' : 'ZY',       'subnets' : ['10.99.101.208/28', '10.99.201.208/28'],                'admin_parent' : 'Z'},
               {'family' : socket.AF_INET, 'uname' : 'ZYA',      'subnets' : ['10.99.101.208/30', '10.99.201.208/30'],                  'admin_parent' : 'ZY'},
               {'family' : socket.AF_INET, 'uname' : 'ZYZ',      'subnets' : ['10.99.101.212/30', '10.99.201.212/30'],                 'admin_parent' : 'ZY'},
               {'family' : socket.AF_INET, 'uname' : 'ZZ',       'subnets' : ['10.99.101.144/28', '10.99.201.144/28'],                 'admin_parent' : 'Z'},
               {'family' : socket.AF_INET, 'uname' : 'ZZA',      'subnets' : ['10.99.101.144/30', '10.99.201.144/30'],                  'admin_parent' : 'ZZ'},
               {'family' : socket.AF_INET, 'uname' : 'ZZZ',      'subnets' : ['10.99.101.148/30', '10.99.201.148/30'],                 'admin_parent' : 'ZZ'},

               # imported Zone from Zorp.Zone
               {'family' : socket.AF_INET6, 'uname' : 'IPv6_Zone_80',  'subnets' : ['fd00:bb:1030:1100:cc::/80'], 'admin_parent' : None},
               {'family' : socket.AF_INET6, 'uname' : 'IPv6_Zone_96',  'subnets' : ['fd00:bb:1030:1100:cc:aa::/96'], 'admin_parent' : None},
               {'family' : socket.AF_INET6, 'uname' : 'IPv6_Zone_96_2',  'subnets' : ['fd00:bb:1030:1100:cc:22::/96'], 'admin_parent' : None},
               {'family' : socket.AF_INET6, 'uname' : 'IPv6_Zone_128',  'subnets' : ['fd00:bb:1030:1100:cc:aa:bb:dd/128'], 'admin_parent' : None},

             ]

    def test_subnet_arith(self):
        self.assertEqual(socket.inet_pton(socket.AF_INET,'192.168.1.1'), testutil.subnet_base(socket.AF_INET,'192.168.1.1/24'))
        self.assertEqual(socket.inet_pton(socket.AF_INET,'255.255.255.0'), testutil.subnet_mask(socket.AF_INET,'192.168.1.1/24'))
        self.assertEqual(socket.inet_pton(socket.AF_INET6,'fd00:bb:1030:1100:cc::'), testutil.subnet_base(socket.AF_INET6,'fd00:bb:1030:1100:cc::/80'))
        self.assertEqual(socket.inet_pton(socket.AF_INET6,'ffff:ffff:ffff:ffff:ffff:0000:0000:0000'), testutil.subnet_mask(socket.AF_INET6,'fd00:bb:1030:1100:cc::/80'))
      
    def _addzones(self):
      for zone in self._zones:
          #print "zone=%s\n"%(zone,)
          subnets = zone['subnets']
          if len(subnets) == 0 :
               self.send_message(kznl.KZorpAddZoneMessage(
                  zone['uname'],
                  family=zone['family'],
                  uname=zone['name'],
                  pname=zone['admin_parent']))
          elif len(subnets) == 1 :
               self.send_message(kznl.KZorpAddZoneMessage(
                  zone['uname'],
                  family=zone['family'],
                  uname=zone['uname'],
                  pname=zone['admin_parent'],
                  address = testutil.subnet_base(zone['family'], zone['subnets'][0]),
                  mask = testutil.subnet_mask(zone['family'], zone['subnets'][0])))
          else:
              self.send_message(kznl.KZorpAddZoneMessage(
                  zone['uname'],
                  family=zone['family'],
                  uname=zone['uname'],
                  pname=zone['admin_parent']))
              for index,subnet in enumerate(subnets):
                self.send_message(kznl.KZorpAddZoneMessage(
                  zone['uname'],
                  family=zone['family'],
                  uname="%s-#%u" % (zone['uname'], index+1),
                  pname=zone['uname'],
                  address = testutil.subnet_base(zone['family'], subnet),
                  mask = testutil.subnet_mask(zone['family'], subnet)))

#          family = zone['family']
#          add_zone_message = KZorpAddZoneMessage(zone['name'],
#                                                 family = family,
#                                                 uname = zone['uname'],
#                                                 pname = zone['pname'],
#                                                 address = socket.inet_pton(family, zone['address']),
#                                                 mask = socket.inet_pton(family, size_to_mask(family, zone['mask'])))
#          self.send_message(add_zone_message)

    def _dump_dispatcher_handler(self, message):
        self._dumped_dispatchers.append(message)

    def check_dispatcher_num(self, num_dispatchers = 0, in_transaction = True):
        self._dumped_dispatchers = []

        if in_transaction == True:
            self.start_transaction()
        self.send_message(kznl.KZorpGetDispatcherMessage(None), message_handler = self._dump_dispatcher_handler, dump = True)
        if in_transaction == True:
            self.end_transaction()

        self.assertEqual(num_dispatchers, len(self._dumped_dispatchers))

    def get_dispatcher_attrs(self, message):
        attrs = message.get_attributes()

        return attrs

    def get_dispatcher_name(self, message):
        attrs = self.get_dispatcher_attrs(message)
        if attrs.has_key(kznl.KZNL_ATTR_DPT_NAME) == True:
            return kznl.parse_name_attr(attrs[kznl.KZNL_ATTR_DPT_NAME])

        return None

    def _check_dispatcher_params(self, add_dispatcher_message, dispatcher_data):
        self.assertEqual(self.get_dispatcher_name(add_dispatcher_message), dispatcher_data['name'])

        attrs = self.get_dispatcher_attrs(add_dispatcher_message)

        num_rules = kznl.parse_n_dimension_attr(attrs[kznl.KZNL_ATTR_DISPATCHER_N_DIMENSION_PARAMS])
        self.assertEqual(dispatcher_data['num_rules'], num_rules)

    def _check_add_rule_params(self, add_dispatcher_message, rule_data):

        attrs = add_dispatcher_message.get_attributes()
        dpt_name, rule_id, service, rules = kznl.parse_rule_attrs(attrs)

        self.assertEqual(rule_data['rule_id'], rule_id)
        self.assertEqual(rule_data['service'], service)

        self.assertEqual(len(rule_data['entry_nums']), len(rules))

        for k, v in rule_data['entry_nums'].items():
            self.assertEqual(k in rules, True)
            self.assertEqual((rule_data['entry_nums'][k],), (rules[k],))

    def _check_add_rule_entry_params(self, add_dispatcher_message, rule_entry_data, rule_entry_index):

        attrs = add_dispatcher_message.get_attributes()
        dpt_name, rule_id, rule_entries = kznl.parse_rule_entry_attrs(attrs)
        self.assertEqual(rule_entry_data['rule_id'], rule_id)
        for k, v in rule_entry_data['entry_values'].items():
            if rule_entry_data['entry_nums'][k] > rule_entry_index:
                self.assertEqual(k in rule_entries, True)
                if k in [kznl.KZNL_ATTR_N_DIMENSION_SRC_IP, kznl.KZNL_ATTR_N_DIMENSION_DST_IP, kznl.KZNL_ATTR_N_DIMENSION_SRC_IP6, kznl.KZNL_ATTR_N_DIMENSION_DST_IP6]:
                    (addr, mask) = rule_entries[k]
                    self.assertEqual(testutil.addr_packed(rule_entry_data['entry_values'][k][rule_entry_index]), addr)
                    self.assertEqual(testutil.netmask_packed(rule_entry_data['entry_values'][k][rule_entry_index]), mask)
                elif k == kznl.KZNL_ATTR_N_DIMENSION_SRC_PORT or k == kznl.KZNL_ATTR_N_DIMENSION_DST_PORT:
                    self.assertEqual(rule_entry_data['entry_values'][k][rule_entry_index], rule_entries[k])
                else:
                    self.assertEqual(rule_entry_data['entry_values'][k][rule_entry_index], rule_entries[k])

    def setup_service_dispatcher(self, services, dispatchers, add_zone = True, add_service = True):
        self._dumped_diszpancsers = []

        self.start_transaction()

        if add_zone:
            self._addzones()

        if add_service:
            for service in services:
                if type(service) == types.DictType:
                    service = service['name']
                self.send_message(kznl.KZorpAddProxyServiceMessage(service))

        for dispatcher in dispatchers:
            message_add_dispatcher = kznl.KZorpAddDispatcherMessage(dispatcher['name'],
                                                               dispatcher['num_rules']
                                                              )

            self.send_message(message_add_dispatcher, error_handler=lambda res: os.strerror(res)+" "+str(message_add_dispatcher))

            for rule in dispatcher['rules']:
                _max = 0
                for name, value in rule['entry_nums'].items():
                    if _max < value:
                        _max = value

                message_add_rule = kznl.KZorpAddRuleMessage(dispatcher['name'],
                                                       rule['rule_id'],
                                                       rule['service'],
                                                       rule['entry_nums']
                                                       )
                self.send_message(message_add_rule)

                for i in range(_max):
                    data = {}
                    for dim_type in kznl.N_DIMENSION_ATTRS:
                        if dim_type in rule['entry_nums'] and rule['entry_nums'][dim_type] > i:
                            if dim_type in [kznl.KZNL_ATTR_N_DIMENSION_SRC_IP, kznl.KZNL_ATTR_N_DIMENSION_DST_IP]:
                                subnet = rule['entry_values'][dim_type][i]
                                data[dim_type] = (testutil.addr_packed(subnet), testutil.netmask_packed(subnet))
                            elif dim_type in [kznl.KZNL_ATTR_N_DIMENSION_SRC_IP6, kznl.KZNL_ATTR_N_DIMENSION_DST_IP6]:
                                subnet = rule['entry_values'][dim_type][i]
                                data[dim_type] = (testutil.addr_packed6(subnet), testutil.netmask_packed6(subnet))
                            else:
                                data[dim_type] = rule['entry_values'][dim_type][i]
                    #print "rule=%s\ndispatcher=%s\ndata=%s\n"%(rule,dispatcher['name'],data)
                    message_add_rule_entry = kznl.KZorpAddRuleEntryMessage(dispatcher['name'], rule['rule_id'], data)

                    self.send_message(message_add_rule_entry)

        self.end_transaction()

if __name__ == "__main__":
    testutil.main()
