import json
import math
from enum import Enum
import ipaddress


class JSONSerialisable(object):
    def json(self):
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, JSONSerialisable):
                result[key] = value.json()
            elif isinstance(value, Enum):
                result[key] = value.name
            elif isinstance(value, list):
                result[key] = [
                    x.json() if isinstance(x, JSONSerialisable) else x for x in value 
                ]
            elif isinstance(value, dict):
                check = lambda v: v.json() if isinstance(v, JSONSerialisable) else v
                result[key] = {
                    k: check(v) for k,v in value.items()
                }
            else:
                result[key] = value
        return result


class DataType(Enum):
    INTEGER = 0
    CUSTOM = 1

class Ignore:
    pass


class ValueOutOfRange(Exception):
    pass

def encodeNum(number, bitwidth):
    if number >= 2 ** bitwidth:
        raise ValueOutOfRange('Value {} has more bits than {}'.format(number, bitwidth))
    byte_len = int(math.ceil(bitwidth / 8.0))
    num_str = '%x' % number
    num_str = '0' * (byte_len * 2 - len(num_str)) + num_str
    return bytes(bytearray.fromhex(num_str))
    

def bytes_to_int(bytes):
    import functools
    # return functools.reduce(lambda x, y: x * 256 + y, [ord(x) for x in bytes]) 
    return functools.reduce(lambda x, y: x * 256 + y, [x for x in bytes]) 


class P4Serialisable(JSONSerialisable):
    ''' The advantage of this class is that data can be stored in a 
    human readable format before being serialised. For instance, IP
    and MAC addresses can be stored as text, rather than a number,
    and the implementation class deals with serialisation '''
    def __new__(cls, *args, **kwargs):
        instance = super(P4Serialisable, cls).__new__(cls)
        instance.bitwidth = cls.bitwidth
        return instance

    def __init__(self, value):
        self.value = value

    def serialise(self):
        return encodeNum(self.value, self.bitwidth)

    @classmethod
    def deserialise(cls, data):
        out = cls(bytes_to_int(data))
        # print(out)
        return out

    def __repr__(self):
        clazz = self.__class__.__name__
        def quoted(value):
            if isinstance(value, str):# or isinstance(value, unicode):
                return '\'{}\''.format(value)
            else:
                return value
        
        pairs = []
        for key, value in self.__dict__.items():
            if key != 'bitwidth':
                pairs.append( '{}={}'.format(key, quoted(value)))
        string = ', '.join(pairs)
        return '{}({})[bitwidth={}]'.format(clazz, string, self.bitwidth)


    
class IPv4Address(P4Serialisable):
    bitwidth = 32

    def __init__(self,
            value,
            mask = encodeNum(2**bitwidth-1, bitwidth),
            prefix_len=0):
        super(IPv4Address, self).__init__(value=value)
        self.mask =  encodeNum(int(ipaddress.ip_address(mask)), 
                IPv4Address.bitwidth)
        self.prefix_len = prefix_len
        # print(self)

    def serialise(self):
        return encodeNum(int(ipaddress.ip_address(self.value)), 
                IPv4Address.bitwidth)

    @classmethod
    def deserialise(cls, data):
        data = ipaddress.ip_address(data).__str__()
        return cls(data)
 

class IPv6Address(P4Serialisable):
    bitwidth = 128

    def __init__(self,
            value,
            mask = encodeNum(2**bitwidth-1, bitwidth),
            prefix_len=0):
        super(IPv6Address, self).__init__(value=value)
        self.mask =  encodeNum(int(ipaddress.ip_address(mask)), 
                IPv6Address.bitwidth)
        self.prefix_len = prefix_len
        # print(self)

    def serialise(self):
        return encodeNum(int(ipaddress.ip_address(self.value)), 
                IPv6Address.bitwidth)

    @classmethod
    def deserialise(cls, data):
        data = ipaddress.ip_address(data).__str__()
        return cls(data)



class MacAddress(P4Serialisable):
    bitwidth = 48

    def serialise(self):
        return bytes(bytearray.fromhex(self.value.replace(':', ''))) #.decode('hex')

    @classmethod
    def deserialise(cls, data):
        return MacAddress(':'.join(['{:02x}'.format(x) for x in data]))
        # result = MacAddress(':'.join(['{:02x}'.format(x) for x in data]))
        # print(result)
        # return result 


class MulticastGroup(P4Serialisable):
    bitwidth = 16



class VlanID(P4Serialisable):
    bitwidth = 12



class EgressSpec(P4Serialisable):
    bitwidth = 9

