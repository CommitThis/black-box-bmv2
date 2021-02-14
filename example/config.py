config = {
    'switch_name': 'meow',
    'network_name': 'meow_net',
    'device_id': 0,
    'election_high': 0,
    'election_low': 1,
	'defaults': {
		'disable_ipv6': True,
		'mtu': 9500,
		'state': 'up'
	},
	'pairs' : [{
		'host': {
			'name': 'h1eth0',
			# 'mac': '20:4E:7F:00:00:01',
			'ip': '10.0.0.1',
		},
		'peer' : {
			'name': 'Ethernet0',
			# 'mac': '84:C7:8F:00:00:01',
			'ip': '10.0.2.1'
		}
	},
	{
		'host': {
			'name': 'h2eth0',
			# 'mac': '20:4E:7F:00:00:02',
			'ip': '10.0.0.2',
		},
		'peer' : {
			'name': 'Ethernet1',
			# 'mac': '84:C7:8F:00:00:02',
			'ip': '10.0.2.2'
		}
	},
	{
		'host': {
			'name': 'h3eth0',
			# 'mac': '20:4E:7F:00:00:03',
			'ip': '10.0.0.3',
		},
		'peer' : {
			'name': 'Ethernet2',
			# 'mac': '84:C7:8F:00:00:03',
			'ip': '10.0.2.3'
		}
	},
	{
		'host': {
			'name': 'h4eth0',
			# 'mac': '20:4E:7F:00:00:04',
			'ip': '10.0.0.4',
		},
		'peer' : {
			'name': 'Ethernet3',
			# 'mac': '84:C7:8F:00:00:04',
			'ip': '10.0.2.4'
		}
	}]
}