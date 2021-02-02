class EntityNotFound(Exception):
    def __init__(self, msg):
        super(Exception, self).__init__(msg)

''' Unused '''
class BadValueType(Exception):
    def __init__(self, msg):
        super(Exception, self).__init__(msg)


class ValueOutOfRange(Exception):
    def __init__(self, msg):
        super(Exception, self).__init__(msg)

''' Unused '''
class WriteError(Exception):
    def __init__(self, msg):
        super(Exception, self).__init__(msg)


class BitwidthsDontMatch(Exception):
    def __init__(self, msg):
        super(Exception, self).__init__(msg) 