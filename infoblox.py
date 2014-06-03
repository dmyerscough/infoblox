#!/usr/bin/env python

import requests
import json


class Infoblox():

    def __init__(self, hostname, username, password, version='1.2.1'):
        '''

        '''
        self.hostname = hostname
        self.username = username
        self.password = password

        self.version = version
        self.session = requests.session()

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
                self.url + obj, data=json.dumps(req),
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

        if res.status_code == 200 or res.status_code == 201:
            if res.content.replace('"', '').startswith(obj):
                return True
            else:
                return res.json()
        else:
            raise Exception(json.loads(res.content)['text'])

    def get_network(self, network):
        '''
        Return network details

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

    def get_host_record(self, hostname):
        '''

        '''
        return self._request('record:host', {'name': hostname}, 'GET')

    def create_fixed_address(self, hostname, ip, mac, comment=''):
        '''
        Create a static IP address

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
        >>> app.get_network('10.224.253.0/28', 2)
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
        '''
        return self._request('range', {'start_addr': start,
                                       'end_addr': end,
                                       'network': network}, 'POST')

if __name__ == '__main__':

    app = Infoblox('https://example.com', 'admin', 'secret', '1.2.1')
    #print app.create_fixed_address('example.com', '10.224.253.1', '90:b1:1c:71:86:e6')
    #print app.get_next_ip('10.224.253.0/28', 2)
    #print app.create_network('10.224.254.0/28', '10.224.43.36', {'name': 'routers', 'value': '10.224.254.1'})
    #print app.create_network('10.224.254.0/28', '10.224.43.36', {'name': 'routers', 'value': '10.224.254.1'})
    #print app.network_range('10.224.254.0/28', '10.224.254.4', '10.224.254.14', '10.224.254.1')
