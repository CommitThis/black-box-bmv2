import google.protobuf.text_format
from p4.config.v1 import p4info_pb2 # Needed for runtime version of Info
from p4.v1 import p4runtime_pb2

from p4client.error import EntityNotFound
from p4client.fields import Ignore

class P4InfoHelper(object):
    ''' 
    P4InfoHelper contains helpers for using P4 Info protobuf objects.

    The class is effectively being used as a namespace; it only contains 
    static methods. The reason for this is that it reduces coupling. In a real
    world example you might expect to have already constructed a P4Info object,
    and it makes no sense to duplicate that state. This would be especially 
    problematic in the case of an info change (e.g. when swapping out a 
    pipeline definition). The gRPC class in this library, for instance, already
    contains a P4Info object.
    '''

    @staticmethod
    def get_tables(self):
        return p4info.tables


    @staticmethod
    def get_table(p4info, table_name):
        for table in p4info.tables:
            if table.preamble.name == table_name:
                return table
        
        raise EntityNotFound('table: {}'.format(table_name))


    @staticmethod
    def get_table_id(p4info, table_name):
        return P4InfoHelper.get_table(p4info, table_name).preamble.id


    @staticmethod
    def get_match_field(p4info, table_name, match_field_name):
        table = P4InfoHelper.get_table(p4info, table_name)
        for match_field in table.match_fields:
            if match_field.name == match_field_name:
                return match_field

        raise EntityNotFound('match field: {}'.format(match_field_name))


    @staticmethod
    def get_match_field_id(p4info, table_name, match_field_name):
        match = P4InfoHelper.get_match_field(p4info, table_name, match_field_name)
        return match.id


    @staticmethod
    def get_action(p4info, action_name):
        for action in p4info.actions:
            if action.preamble.name == action_name:
                return action
        
        raise EntityNotFound('action: {}'.format(action_name))


    @staticmethod
    def get_action_id(p4info, action_name):
        action = P4InfoHelper.get_action(p4info, action_name)
        return action.preamble.id


    @staticmethod
    def get_action_param(p4info, action_name, param_name):
        action = P4InfoHelper.get_action(p4info, action_name)
        for param in action.params:
            if param.name == param_name:
                return param

        raise EntityNotFound('action param: {}'.format(param_name))


    @staticmethod
    def get_action_param_id(p4info, action_name, param_name):
        param = P4InfoHelper.get_action_param(p4info, action_name, param_name)
        return action.id


    @staticmethod
    def get_digest(p4info, digest_name):
        # for digest in p4info.digests:
        for digest in p4info.digests:
            if digest.preamble.name == digest_name:
                return digest
        
        raise EntityNotFound('digest: {}'.format(digest_name))


    @staticmethod
    def get_digest_id(p4info, digest_name):
        return P4InfoHelper.get_digest(p4info, digest_name).preamble.id


    @staticmethod
    def create_stream_message_request(digest_id, list_id):
        runtime_request = p4runtime_pb2.StreamMessageRequest()
        digest_ack = request.digest_ack
        digest_ack.digest_id = digest_id
        digest_ack.list_id = list_id
        return runtime_request


    @staticmethod
    def create_write_request(device_id, election_low, election_high):
        runtime_request = p4runtime_pb2.WriteRequest()
        runtime_request.device_id = device_id
        runtime_request.election_id.low = election_low
        runtime_request.election_id.high = election_high
        return runtime_request


    @staticmethod
    def create_match_field(p4info, table_name, field_name, data):
        info_match = P4InfoHelper.get_match_field(p4info, table_name, field_name)
        runtime_match = p4runtime_pb2.FieldMatch()
        runtime_match.field_id = info_match.id

        # if isinstance(data, Ignore):
        #     # need handle ternary lpm
        #     return runtime_match

        if data.bitwidth != info_match.bitwidth:
            class_name = data.__class__.__name__
            raise BitwidthsDontMatch('Bitwidth for {} is {} but P4 expected {}.'.format(
                class_name,
                data.bitwidth,
                info.bitwitdh
            ))

        else:
            if p4info_pb2.MatchField.EXACT == info_match.match_type:
                runtime_match.exact.value = data.serialise()

            elif p4info_pb2.MatchField.LPM == info_match.match_type:
                runtime_match.lpm.value = data.serialise()
                runtime_match.lpm.prefix_len = data.prefix_len

            elif p4info_pb2.MatchField.TERNARY == info_match.match_type:
                runtime_match.ternary.value = data.serialise()
                runtime_match.ternary.mask = data.mask


        # elif p4info_pb2.MatchField.TERNARY == info_match.match_type:
        #     if int.from_bytes(data.mask, byteorder='little') != 0:
        #         runtime_match.ternary.value = data.serialise()
        #         runtime_match.ternary.mask = data.mask
        #     else:
        #         # pass
        #         # Omit entry
        #         field_match = p4runtime_pb2.FieldMatch.Ternary()
        #         runtime_match.ternary.CopyFrom(field_match)

        return runtime_match
    

    @staticmethod
    def create_match_fields(p4info, table_name, match_fields):
        runtime_match_fields = []
        for match_field_name, match_field_data in match_fields.items():
            match = P4InfoHelper.create_match_field(p4info, table_name,
                    match_field_name, match_field_data)
            runtime_match_fields.append(match)
        return runtime_match_fields


    @staticmethod
    def create_digest_entry(p4info, 
            digest_name,
            max_timeout,
            max_list_size,
            ack_timeout):
        runtime_digest_entry = p4runtime_pb2.DigestEntry()
        runtime_digest_entry.digest_id = P4InfoHelper.get_digest_id(p4info,
                digest_name)
        runtime_digest_entry.config.max_timeout_ns = max_timeout
        runtime_digest_entry.config.max_list_size = max_list_size
        runtime_digest_entry.config.ack_timeout_ns = ack_timeout
        return runtime_digest_entry


    @staticmethod
    def create_digest_acknowledgement(digest_id, list_id):
        runtime_ack = p4runtime_pb2.StreamMessageRequest()
        digest_ack = runtime_ack.digest_ack
        digest_ack.digest_id = digest_id
        digest_ack.list_id = list_id
        return runtime_ack


    @staticmethod
    def create_action_param(p4info, action_name, param_name, param_value):
        info_param = P4InfoHelper.get_action_param(p4info, action_name,
                param_name)
        runtime_param = p4runtime_pb2.Action.Param()
        runtime_param.param_id = info_param.id
        runtime_param.value = param_value.serialise()
        return runtime_param


    @staticmethod
    def create_action(p4info, action_name, action_params):
        info_action = P4InfoHelper.get_action(p4info, action_name)
        runtime_action = p4runtime_pb2.Action()
        runtime_action.action_id = info_action.preamble.id

        if action_params is not None:
            for param_name, param_value in action_params.items():
                runtime_param = P4InfoHelper.create_action_param(p4info, 
                    info_action.preamble.name,
                    param_name,
                    param_value)
                runtime_action.params.extend([runtime_param])

        return runtime_action


    @staticmethod
    def create_multicast_group_entry(group_id, replicas):
        mc_group_entry = p4runtime_pb2.MulticastGroupEntry()
        mc_group_entry.multicast_group_id = group_id

        for replica in replicas:
            runtime_replica = p4runtime_pb2.Replica()
            runtime_replica.egress_port = replica['egress_port']
            runtime_replica.instance = replica['instance']
            mc_group_entry.replicas.extend([runtime_replica])

        return mc_group_entry


    @staticmethod
    def create_table_entry(p4info, table_name=None):
        table_id = P4InfoHelper.get_table_id(p4info, table_name) if table_name is not None else 0
        runtime_table_entry = p4runtime_pb2.TableEntry()
        runtime_table_entry.table_id = table_id
        return runtime_table_entry
