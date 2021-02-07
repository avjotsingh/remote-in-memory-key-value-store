"""Python implementation of KeyValue service"""

from concurrent import futures
import grpc
import logging

import keyval_pb2
import keyval_pb2_grpc

class KeyValueServicer(keyval_pb2_grpc.KeyValueServicer):
    """Provides methods that implement the functionality of the Key Value server"""

    def __init__(self):
        self.keyval_store = {}

    def Read(self, request, context):
        key = request.key
        status = keyval_pb2.Status(server_id=1, ok=True, error="")
        return keyval_pb2.ReadResponse(status=status, key=key, value=self.keyval_store[key]["value"], current_version=self.keyval_store[key]["version"])

    def Write(self, request, context):
        key = request.key
        value = request.value
        version = request.current_version
        self.keyval_store[key] = {"value": value, "version": version}

        status = keyval_pb2.Status(server_id=1, ok=True, error="")
        return keyval_pb2.WriteResponse(status=status, key=key, new_version=version)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    keyval_pb2_grpc.add_KeyValueServicer_to_server(KeyValueServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig()
    serve()