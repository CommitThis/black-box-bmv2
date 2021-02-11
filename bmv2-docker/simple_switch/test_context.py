import pytest
import time

from threading import Thread
from threading import Event

from p4client.p4grpc import P4RuntimeGRPC
from packettest.test_context import TestContext
from simple_switch.simple_switch_runner import make_switch

merged_config = {
    'switch_name': 'meow',
    'network_name': 'meow_net',
    'device_id': 0,
    'election_high': 0,
    'election_low': 1,
    'grpc_port': 9559
}



def make_bmv_context(config, compiled, p4info, control_function=None,
        configure=None, log_level='info'):
    merged_config.update(config)

    @pytest.fixture(scope='module')
    def context_():
        bmv2 = make_switch(config, 
            merged_config.get('switch_name'),
            merged_config.get('network_name'),
            merged_config.get('grpc_port'))

        bmv2.launch(log_level=log_level)

        continue_event = Event()
        shutdown_event = Event()

        def wait_start_and_log_stream():
            ''' Start reading the logs and trigger an event when the switch
            application has started the thrift server to test for readiness.
            While not perfect as it isn't testing the gRPC interface, it is a
            good (read: only) proxy for doing so.'''

            for line in bmv2.stream():
                line = line.decode('utf-8').strip()
                if 'Thrift server was started' in line:
                    continue_event.set()
                print(line)


        logs = Thread(target=wait_start_and_log_stream)
        logs.start()
        continue_event.wait()

        grpc_port = merged_config.get('grpc_port')
        controller = P4RuntimeGRPC(
            host=f'localhost:{grpc_port}',
            device_id=merged_config.get('device_id'),
            election_high=merged_config.get('election_high'),
            election_low=merged_config.get('election_low')
        )

        controller.master_arbitration_update()
        info_data = open(p4info, 'rb').read()
        bin_data = open(compiled, 'rb').read()
        controller._set_info(info_data)
        controller.configure_forwarding_pipeline(bin_data)


        if configure is not None:
            configure(controller)

        if control_function is not None:
            controller_thread = Thread(target=control_function, args=[
                    controller,
                    shutdown_event])
            controller_thread.start()

        time.sleep(1)

        yield TestContext()

        if controller is not None:
            controller.tear_down_stream()
        bmv2.kill()
        shutdown_event.set()
        if controller is not None:
            controller_thread.join()
        logs.join()
    return context_