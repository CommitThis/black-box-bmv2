import json
import math
from enum import Enum


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
        return cls(bytes_to_int(data))

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

    def __init__(self, value):
        super(IPv4Address, self).__init__(value=value)

    def serialise(self):
        return int(ipaddress.ip_address(self.value))

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
        result = MacAddress(':'.join(['{:02x}'.format(x) for x in data]))
        return result 


class MulticastGroup(P4Serialisable):
    bitwidth = 16



class VlanID(P4Serialisable):
    bitwidth = 12



class EgressSpec(P4Serialisable):
    bitwidth = 9

