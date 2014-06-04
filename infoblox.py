#!/usr/bin/env python

import requests
import json


__author__ = 'Damian Myerscough'


class Infoblox():

    def __init__(self, hostname, username, password, version='1.2.1'):
        '''

        '''
        self.hostname = hostname
        self.username = username
        self.password = password

        self.version = version
        self.session = requests.session()

        self._RECORDS = ['A', 'AAAA', 'CNAME', 'HOST',
                         'MX', 'PTR', 'SRV', 'TXT']

        self.url = '{0}/wapi/v{1}/'.format(hostname, version)

    def __repr__(self):
        '''
        String representation of the Infoblox object

        >>> app = Infoblox('https://example.com', 'admin', 'secret')
        >>> app
        <Infoblox: https://example.com/wapi/v1.0/>
        '''
        return '<Infoblox: {0}>'.format(self.url, self.version)

    def _request(self, obj, req, method):
        '''
        Handle the REST requests to Infoblox
        '''
        if method.upper() == 'GET':
            res = self.session.get(
                self.url + obj,
                data=json.dumps(req),
                verify=False,
                auth=(self.username, self.password)
            )
        elif method.upper() == 'POST':
            res = self.session.post(
                self.url + obj,
                data=json.dumps(req),
                verify=False,
                auth=(self.username, self.password)
            )
        elif method.upper() == 'DELETE':
            res = self.session.delete(
                self.url + obj,
                verify=False,
                auth=(self.username, self.password)
            )

        if res.status_code == 200 or res.status_code == 201:
            if res.content.replace('"', '').startswith(obj):
                return True
            else:
                return res.json()
        else:
            raise Exception(json.loads(res.content)['text'])

    def delete_record(self, record, record_type):
        '''
        Delete DNS record

        :param record
        The DNS record that you would like to remove

        :param record_type
        The DNS record type

        >>> app = Infoblox('https://example.com', 'admin', 'secret')
        >>> app.delete_record('example.rollback.sfdc.net', 'host')
        True
        '''
        ref = self.get_record(record, record_type)

        if ref:
            return self._request(ref[0]['_ref'], {}, 'DELETE')
        else:
            raise Exception('Unable to delete {0}'.format(record))

    def get_network(self, network):
        '''
        Return network details

        :param network
        The network you would like to get information on

        >>> app = Infoblox('https://example.com', 'admin', 'secret')
        >>> app.get_network('10.224.253.0/28')
        [{u'comment': u'Damian Test', u'_ref':
          u'network/ZG5zLm5ldHdvcmskMTAuMjI0LjI1My4wLzI4LzA:10.224.253.0/28/default',
          u'network': u'10.224.253.0/28',
          u'network_view': u'default'}]
        '''
        return self._request('network', {'network': network}, 'GET')

    def create_network(self, network, grid=False, options={}):
        '''
        Create a network

        :param network
        The network you would like to create

        :param grid
        The Grid member you want to associate the network with

        :param options
        Additional options to override the Grid settings


        >>> app = Infoblox('https://example.com', 'admin', 'secret')
        >>> app.get_network('10.224.254.0/28')
        True

        Create a network and assign the network to a graid master (10.1.1.1)

        >>> app = Infoblox('https://example.com', 'admin', 'secret')
        >>> app.get_network('10.224.254.0/28', '10.1.1.1')
        True

        Create a network and override default routers value

        >>> app = Infoblox('https://example.com', 'admin', 'secret')
        >>> app.get_network('10.224.254.0/28', '10.1.1.1', {'name': 'routers',
        ...                                                'value': 'x.x.x.x'})
        True

        Supported Options
        =================

        * Modify Routers option
        {'name': 'routers', 'value': '10.224.254.1'}

        * Modify dhcp-lease-time
        {'name': 'dhcp-lease-time', 'value': '6000'}

        * Modify domain name
        {'name': 'domain-name', 'value': 'ictest.local'}

        * Modify NTP servers
        {'name': 'ntp-servers', 'value': 'x.x.x.x'}
        '''
        if options and isinstance(options, dict):
            opts = {'use_option': True, 'vendor_class': 'DHCP'}
            opts.update(options)

        if grid:
            if options:
                data = {'network': network,
                        'options': [options],
                        'members': [{'_struct': 'dhcpmember',
                                     'ipv4addr': grid}]}
            else:
                data = {'network': network,
                        'members': [{'_struct': 'dhcpmember',
                                     'ipv4addr': grid}]}

            return self._request('network', data, 'POST')
        else:
            if options:
                data = {'network': network,
                        'options': [options]}
            else:
                data = {'network': network}

            return self._request('network', data, 'POST')

    def get_record(self, record, record_type):
        '''
        Get DNS record

        :param record
        The record you would like to retrieve

        :param record_type
        The record type

        >>> app = Infoblox('https://example.com', 'admin', 'secret')
        >>> app.get_record('myhost.example.com', 'host')
        [{u'_ref': u'record:host/ZG5zLmhvc3QkLl9kZWZhdWx0Lm5ldC5zZmRjLnJvbGxiYWNrLmV4YW1wbGU:myhost.example.com/default',
          u'name': u'myhost.example.com',
          u'ipv4addrs': [{u'configure_for_dhcp': False,
                          u'_ref': u'record:host_ipv4addr/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubmV0LnNmZGMucm9sbGJhY2suZXhhbXBsZS4xMC4wLjAuMS4:10.0.0.1/myhost.example.com/default',
                          u'ipv4addr': u'10.0.0.1',
                          u'host': u'myhost.example.com'}],
         u'view': u'default'}]
        '''
        if record_type in self._RECORDS:
            return self._request('record:' + record_type, {'name': record}, 'GET')
        else:
            raise Exception('unsupported record type {0}'.format(record_type))

    def create_record(self, record_type, record, data):
        '''
        Create a DNS record

        :param record
        DNS record to create

        :param record_type
        DNS record type to use
        '''
        _options = {'A': {'name': record,
                          'ipv4addr': data},
                    'AAAA': {'name': record,
                             'ipv6addr': data},
                    'CNAME': {'name': record,
                              'canonical': data},
                    'HOST': {'name': record,
                             'ipv4addrs': [{'ipv4addr': data}]},
                    'PTR': {'name': record,
                            'ipv4addr': data,
                            'ptrdname': record},
                    'TXT': {'name': record,
                            'text': data}}

        # since MX records require multiple arguments we need them to be
        # passed over as a dictionary
        if isinstance(data, dict):
            _options.update({'MX': {'name': record,
                           'mail_exchanger': data['mail_exchanger'],
                           'preference': data['preference']})

        if record_type in self._RECORDS:
            return self._request('record:' + record_type.lower(),
                                 _options[record_type.upper()], 'POST')
        else:
            raise Exception('unsupported record type {0}'.format(record_type))

    def create_fixed_address(self, hostname, ip, mac, comment=''):
        '''
        Create a static IP address

        :param hostname
        Systems hostname you would like to set

        :param ip
        Systems desired IP address

        :param mac
        Systems MAC address

        :param comment
        Comments to be associated with the static address

        >>> app = Infoblox('https://example.com', 'admin', 'secret')
        >>> app.create_fixed_address('ops-test1-1-sfm.rollback.sfdc.net',
            '10.224.253.1', '90:b1:1c:71:86:e6'
        )
        True
        '''
        return self._request('fixedaddress', {'name': hostname,
                                              'ipv4addr': ip,
                                              'mac': mac,
                                              'comment': comment}, 'POST')

    def get_next_ip(self, network, n=1):
        '''
        Get the next available IP address or get a list of the next available
        IP addresses

        >>> app = Infoblox('https://example.com', 'admin', 'secret')
        >>> app.get_next_ip('10.224.253.0/28', 2)
        {u'ips': [u'10.224.253.2', u'10.224.253.3']}
        '''
        try:
            return self._request(
                self.get_network(network)[0]['_ref'] +
                '?_function=next_available_ip',
                {'num': n}, 'POST'
            )
        except IndexError:
            raise Exception('Unable to retrieve next available IP \
                            address for {0}'.format(network))

    def network_range(self, network, start, end):
        '''
        Reserve DHCP IP range for a specific network

        :param network
        The network you want to reserve IP addresses on

        :param start
        The starting IP address to be reserved

        :param end
        The end IP address to be reserved

        >>> app = Infoblox('https://example.com', 'admin', 'secret')
        >>> app.network_range('10.224.254.0/28', '10.224.254.4', '10.224.254.14')
        True
        '''
        return self._request('range', {'start_addr': start,
                                       'end_addr': end,
                                       'network': network}, 'POST')

    def get_grid(self):
        '''
        Get a list of Grid Members

        >>> app = Infoblox('https://example.com', 'admin', 'secret')
        >>> app.get_grid()
        [{u'_ref': u'member/b25lLnZpcnR1YWxfbm9kZSQw:example.com',
          u'host_name': u'mygrid.example.com'}]
        '''
        return self._request('member', {}, 'GET')


if __name__ == '__main__':

    app = Infoblox('https://example.com', 'admin', 'secret')
    #print app.create_fixed_address('example.com', '10.224.253.1', '90:b1:1c:71:86:e6')
    #print app.get_next_ip('10.224.253.0/28', 2)
    #print app.create_network('10.224.254.0/28', '10.224.43.36', {'name': 'routers', 'value': '10.224.254.1'})
    #print app.create_network('10.224.254.0/28', '10.224.43.36', {'name': 'routers', 'value': '10.224.254.1'})
    #print app.network_range('10.224.254.0/28', '10.224.254.4', '10.224.254.14', '10.224.254.1')
    #print app.get_record('myhost.example.com', 'host')
    #print app.delete_record('myhost.example.com', 'host')
    #print app.create_record('A', 'myhost.example.com', '10.0.0.1')
    #print app.create_record('CNAME', 'myhost1.example.com', 'myhost.example.com')
    #print app.create_record('PTR', 'myhost.example.com', '10.0.0.1')
    #print app.create_record('TXT', 'myhost.example.com', 'THIS IS A TEST')
    #print app.create_record('HOST', 'myhost.example.com', '10.0.0.3')
    #print app.create_record('MX', 'myhost.example.com', {'mail_exchanger': '10.0.0.1', 'preference': 20})
