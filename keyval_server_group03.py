"""Python implementation of KeyValue service"""

from concurrent import futures
import grpc
import logging
import sys
import argparse

import keyval_pb2
import keyval_pb2_grpc

class KeyValueServicer(keyval_pb2_grpc.KeyValueServicer):
    """Provides methods that implement the functionality of the Key Value server"""

    def __init__(self):
        self.keyval_store = {}

    def Read(self, request, context):
        key = request.key
        if key is None:
            status = keyval_pb2.Status(server_id=SERVER_ID, ok=False, error='Invalid read proto')
            return keyval_pb2.ReadResponse(status=status)
        elif key not in self.keyval_store:
            status = keyval_pb2.Status(server_id=SERVER_ID, ok=False, error='Read aborted. Key not aborted %s'%key)
            return keyval_pb2.ReadResponse(status=status)
        else:
            status = keyval_pb2.Status(server_id=SERVER_ID, ok=True)
            return keyval_pb2.ReadResponse(status=status, key=key, value=self.keyval_store[key]['value'], current_version=self.keyval_store[key]['version'])
        
    def Write(self, request, context):
        key = request.key
        value = request.value
        current_version = request.current_version
        if key is None or current_version == 0:
            status = keyval_pb2.Status(server_id=SERVER_ID, ok=False, error='Invalid write proto')
            return keyval_pb2.WriteResponse(status=status)
        elif value is None:
            status = keyval_pb2.Status(server_id=SERVER_ID, ok=False, error='Write aborted. Record missing but Write expected value to exist at version %d'%self.keyval_store[key]['version'])
            return keyval_pb2.WriteResponse(status=status, key=key, new_version=current_version+1)
        elif current_version < 0:
            self.keyval_store[key] = {'value': value, 'version': 1}
            status = keyval_pb2.Status(server_id=SERVER_ID, ok=True)
            return keyval_pb2.WriteResponse(status=status, key=key, new_version=1)
        elif current_version == self.keyval_store[key]['version']:
            new_version = current_version + 1
            self.keyval_store[key]['version'] = new_version
            status = keyval_pb2.Status(server_id=SERVER_ID, ok=True)
            return keyval_pb2.WriteResponse(status=status, key=key, new_version=new_version)
        else:
            status = keyval_pb2.Status(server_id=SERVER_ID, ok=False, error='Write aborted. Record version mismatch. Expected = %d, Actual = %d'%(current_version, self.keyval_store[key]['version']))
            return keyval_pb2.WriteResponse(status=status, key=key, new_version=self.keyval_store[key]['version'])

    def Delete(self, request, context):
        key = request.key
        current_version = request.current_version
        if key is None or current_version == 0:
            status = keyval_pb2.Status(server_id=SERVER_ID, ok=False, error='Delete proto invalid')
            return keyval_pb2.DeleteResponse(status=status)
        elif key not in self.keyval_store:
            status = keyval_pb2.Status(server_id=SERVER_ID, ok=False, error='Delete aborted. Key not present %s'%key)
            return keyval_pb2.DeleteResponse(status=status)
        elif current_version < 0 or self.keyval_store[key]['version'] == current_version:
            deleted_value = self.keyval_store[key]['value']
            deleted_version = self.keyval_store[key]['version']
            status = keyval_pb2.Status(server_id=SERVER_ID, ok=True)
            return keyval_pb2.DeleteResponse(status=status, key=key, deleted_value=deleted_value, deleted_version=deleted_version)
        else:
            status = keyval_pb2.Status(server_id=SERVER_ID, ok=False, error='Delete aborted. Record version mismatch. Expected = %d, Actual = %d'%(self.keyval_store[key]['version'], current_version))
            return keyval_pb2.DeleteResponse(status=status)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    keyval_pb2_grpc.add_KeyValueServicer_to_server(KeyValueServicer(), server)
    server.add_insecure_port('localhost:%s'%PORT_NO)
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='KeyVal Server arguments')
    parser.add_argument('--server_id', type=int, help='The id of the server.', default=1)
    parser.add_argument('--write_delay', type=int, help='The delay in seconds that is added to the Write RPC handling in the server,\
         i.e., before the Write RPC is handled on the server side.')
    parser.add_argument('--port', type=int, help='The port on which the server listens.', default=50050)
    args = parser.parse_args()

    SERVER_ID = args.server_id
    WRITE_DELAY = args.write_delay
    PORT_NO = args.port

    logging.basicConfig()
    serve()