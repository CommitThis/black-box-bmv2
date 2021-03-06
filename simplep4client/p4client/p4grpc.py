from abc import abstractmethod
from datetime import datetime
import argparse
import sys
import grpc
import time
import json

from p4.v1 import p4runtime_pb2
from p4.v1 import p4runtime_pb2_grpc
from p4.config.v1 import p4info_pb2

# from p4info import P4Info
import google.protobuf.text_format
import google.protobuf.json_format

from queue import Queue
from queue import Empty # Possibly bad, a bit vague to bring into module
from threading import Thread
from enum import Enum


from p4client.p4info import P4InfoHelper


class IterableQueue(Queue):
    _sentinel = object()

    def __iter__(self):
        return iter(self.get, self._sentinel)

    def close(self):
        self.put(self._sentinel)


class WorkerStatus(Enum):
    STARTING = 'starting'
    RUNNING = 'running'
    ERROR = 'error'
    SHUTDOWN = 'shutdown'


class UpdateType(Enum):
    INSERT = 'insert'
    UPDATE = 'update'



def get_pb2_update(update_type):
    return {
        UpdateType.INSERT: p4runtime_pb2.Update.INSERT,
        UpdateType.UPDATE: p4runtime_pb2.Update.MODIFY,
    }[update_type]


def seconds(value):
    return int(value * 1000000000)



class P4RuntimeGRPC(object):

    def __init__(self, host, device_id, election_high, election_low):
        self._info = None
        self._host = host
        self._error = None
        self._device_id = device_id
        self._election_high = election_high
        self._election_low = election_low
        self._status = None
        self.start()


    def start(self):
        self._status = WorkerStatus.STARTING
        self._error = None
        self._channel = grpc.insecure_channel(self._host, options=(('grpc.enable_http_proxy', 0),))
        self._client = p4runtime_pb2_grpc.P4RuntimeStub(self._channel)
        self._setup_stream()


    def status(self):
        return {
            'status': str(self._status),
            'error': str(self._error),
            'device_id': self._device_id,
            'election_high': self._election_high,
            'election_low': self._election_low
        }


    def _set_info(self, p4info_data):
        print('set info')
        self._info = p4info_pb2.P4Info()
        google.protobuf.text_format.Merge(p4info_data, self._info)


    def _setup_stream(self):
        print('setup stream')
        self._stream_out_q = Queue() # Stream request channel (self._stream), 
        self._stream_in_q = Queue() # Receiving messages from device

        def stream_req_iterator():
            ''' If the queue is populated, take one and yield it. Being
            iterable, the function will carry on. if None is received, the
            generator will end '''
            while True:
                p = self._stream_out_q.get()
                if p is None:
                    break
                yield p

        def stream_recv(stream):
            self._status = WorkerStatus.RUNNING
            print('stream receive')
            try:
                for p in stream:
                    self._stream_in_q.put(p)
            except Exception as e:
                self._status = WorkerStatus.ERROR
                self._error = str(e)
                print(str(e))
            print('end stream receive')

        self._stream = self._client.StreamChannel(stream_req_iterator())
        self._stream_recv_thread = Thread(target=stream_recv, 
                args=(self._stream,))
        self._stream_recv_thread.start()


    def __get_write_request(self):
        ''' This does not follow the usual pattern of having the PB 
        creation functions in the helper as it is way easier to do here
        and removes a lot of code bloat'''
        runtime_request = p4runtime_pb2.WriteRequest()
        runtime_request.device_id = self._device_id
        runtime_request.election_id.low = self._election_low
        runtime_request.election_id.high = self._election_high
        return runtime_request


    def tear_down_stream(self):
        self._stream_out_q.put(None)
        self._stream_recv_thread.join()
        self._status = WorkerStatus.SHUTDOWN


    def get_message(self, timeout=10):
        try:
            message = self._stream_in_q.get(block=True, timeout=timeout)
            self._stream_in_q.task_done()
            return message
        except Empty:
            return None
        

    def master_arbitration_update(self):
        request = p4runtime_pb2.StreamMessageRequest()
        request.arbitration.device_id = self._device_id
        request.arbitration.election_id.high = self._election_high
        request.arbitration.election_id.low = self._election_low
        self._stream_out_q.put(request)


    def configure_forwarding_pipeline(self, pipeline_data):
        request = p4runtime_pb2.SetForwardingPipelineConfigRequest()
        request.device_id = self._device_id
        request.election_id.high = self._election_high
        request.election_id.low = self._election_low
        config = request.config
        config.p4info.CopyFrom(self._info)
        config.p4_device_config = pipeline_data
        request.action = p4runtime_pb2.SetForwardingPipelineConfigRequest.VERIFY_AND_COMMIT
        # SetForwardingPipelineConfigResponse exists but is empty
        self._client.SetForwardingPipelineConfig(request)


    def read_table_entries(self, table_id=None):
        request = p4runtime_pb2.ReadRequest()
        request.device_id = self._device_id
        entity = request.entities.add()
        table_entry = entity.table_entry
        if table_id is not None:
            table_entry.table_id = table_id
        else:
            table_entry.table_id = 0

        for response in self._client.Read(request):
            yield response


    def read_counters(self, counter_id=None, index=None):
        request = p4runtime_pb2.ReadRequest()
        request.device_id = self._device_id
        entity = request.entities.add()
        counter_entry = entity.counter_entry
        if counter_id is not None:
            counter_entry.counter_id = counter_id
        else:
            counter_entry.counter_id = 0
        if index is not None:
            counter_entry.index.index = index

        for response in self._client.Read(request):
            yield response


    def acknowledge_digest_list(self, digest_id, list_id):
        ''' If using queues for incoming, if our processing queue is full
        we might be able to wait before the queue is empty or occupied by
        some factor before acknowledging the digest list message '''
        runtime_ack = P4InfoHelper.create_digest_acknowledgement(digest_id,
                list_id)
        self._stream_out_q.put(runtime_ack)


    def capabilities(self):
        request = p4runtime_pb2.CapabilitiesRequest()
        response = self._client.Capabilities(request)
        return response.p4runtime_api_version


    def add_digest_entry(self, 
                digest_name, 
                max_timeout=seconds(0.001), 
                max_list_size=5, 
                ack_timeout=seconds(1)):
        request = self.__get_write_request()
        digest_entry = P4InfoHelper.create_digest_entry(self._info, digest_name, max_timeout, 
                max_list_size, ack_timeout)

        update = request.updates.add()
        update.type = p4runtime_pb2.Update.INSERT
        update.entity.digest_entry.CopyFrom(digest_entry)

        try:
            # WriteResponse exists but is empty
            self._client.Write(request)
        except grpc.RpcError as e:
            raise Exception(e.details())


    def write_table(self,
            table_name, 
            match_fields, 
            action_name=None, 
            action_params=None,
            meter_config=None,
            priority=None):
        runtime_request = self.__get_write_request()
        table_entry = P4InfoHelper.create_table_entry(self._info,
                table_name)
        runtime_matches = P4InfoHelper.create_match_fields(self._info,
                table_name, match_fields)

        table_entry.match.extend(runtime_matches)

        if action_name != None:
            runtime_action = P4InfoHelper.create_action(self._info, action_name,
                    action_params)
            table_entry.action.action.CopyFrom(runtime_action)

        if priority != None:
            table_entry.priority = priority
            
        # if meter_config != None:
        #     meter_config = p4runtime_pb2.MeterConfig(
        #         cir=meter_config['cir'],
        #         cburst=meter_config['cburst'],
        #         pir=meter_config['pir'],
        #         pburst=meter_config['pburst'])
        #     table_entry.meter_config.CopyFrom(meter_config)
            

        update = runtime_request.updates.add()
        update.type = p4runtime_pb2.Update.INSERT
        update.entity.table_entry.CopyFrom(table_entry)
        
        self._client.Write(runtime_request)


    def read_direct_meters(self, table_name=None):
        table_id = P4InfoHelper.get_table_id(self._info, table_name)

        entity = p4runtime_pb2.Entity()
        table_entry = p4runtime_pb2.TableEntry(table_id=table_id)
        entity.table_entry.CopyFrom(table_entry)

        request = p4runtime_pb2.ReadRequest(device_id=self._device_id,
            entities=[entity])

        for response in self._client.Read(request):
            print("-----\n", response, '\n------')


        # request.device_id = self._device_id
        # entity = request.entities.add()

        # # Table id 0 (all tables)
        # table_entry = P4InfoHelper.create_table_entry(self._info, table_name)
        # entity.direct_meter_entry.table_entry.CopyFrom(table_entry)
        # print(request.device_id)
        # print(request)
        # self._client.Write(request)


    def write_direct_meter(self, table_name, cir, cburst, pir, pburst,
            match_fields):
        request = self.__get_write_request()
        request.device_id = self._device_id

        meter_config = p4runtime_pb2.MeterConfig(cir=cir,
            cburst=cburst,
            pir=pir,
            pburst=pburst)

        table_entry = P4InfoHelper.create_table_entry(self._info,
                table_name)

        matches = P4InfoHelper.create_match_fields(self._info,
                table_name, match_fields)

        table_entry.match.extend(matches)
        table_entry.meter_config.CopyFrom(meter_config)


        update = request.updates.add()
        update.type = p4runtime_pb2.Update.MODIFY
        update.entity.direct_meter_entry.table_entry.CopyFrom(table_entry)
        update.entity.direct_meter_entry.config.CopyFrom(meter_config)

        self._client.Write(request)


    def write_multicast(self, group_id, replicas, update_type=UpdateType.INSERT):
        runtime_request = self.__get_write_request()
        entry = P4InfoHelper.create_multicast_group_entry(group_id,
                replicas)

        update = runtime_request.updates.add()
        update.type = get_pb2_update(update_type) #p4runtime_pb2.Update.INSERT
        update.entity.packet_replication_engine_entry.multicast_group_entry.CopyFrom(entry)

        self._client.Write(runtime_request)



    def read_table(self, table_name):
        runtime_request = p4runtime_pb2.ReadRequest()
        runtime_request.device_id = self._device_id
        entity = runtime_request.entities.add()
        table_entry = entity.table_entry
        table_entry.table_id = P4InfoHelper.get_table_id(self._info, table_name)

        return [resp for resp in self._client.Read(runtime_request)]

