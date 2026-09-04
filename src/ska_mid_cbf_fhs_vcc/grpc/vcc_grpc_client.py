from ska_mid_cbf_fhs_common import FirmwareApi, GRPCInfo
from ska_mid_cbf_fhs_vcc_grpc_controller.generated.vcc_drivers import vcc_drivers_pb2, vcc_drivers_pb2_grpc


class VccGrpcClient(FirmwareApi):

    def __init__(self, firmware_ip_block_id, logger, host, port):

        logger.info(f"[VccGrpcClient.__init__] - CREATING VCCGRPC CLIENT FOR {firmware_ip_block_id}")

        self.grpc_info = GRPCInfo(
            pb2_class=vcc_drivers_pb2, pb2_grpc_class=vcc_drivers_pb2_grpc, pb2_grpc_stub_class=vcc_drivers_pb2_grpc.VccFpgaDriverStub, host=host, port=port
        )

        super().__init__(firmware_ip_block_id, logger, self.grpc_info)
