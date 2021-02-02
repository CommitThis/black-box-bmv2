from p4client import p4grpc


def load_program(host, program, device_id, election_high=0, election_low=1):
    controller = P4RuntimeGRPC(
            host=host,
            device_id=device_id,
            election_high=election_high,
            election_low=election_low)
    controller.master_arbitration_update()
    controller.configure_forwarding_pipeline(bin_data)
