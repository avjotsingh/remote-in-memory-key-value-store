"""Python implementation of KeyValue service"""

from concurrent import futures

import grpc
from grpc_reflection.v1alpha import reflection

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
        # Check if read proto is invalid
        if key is None or key == '':
            status = keyval_pb2.Status(server_id=SERVER_ID, ok=False, error='Invalid read proto ')
            return keyval_pb2.ReadResponse(status=status)
        
        # Check for erroneous conditions
        # Check if trying to read a key, but the key does not exist
        if key not in self.keyval_store:
            status = keyval_pb2.Status(server_id=SERVER_ID, ok=False, error='Read aborted. Key not present %s'%key)
            return keyval_pb2.ReadResponse(status=status)
        
        # Read request is valid. Perform the read operation
        status = keyval_pb2.Status(server_id=SERVER_ID, ok=True)
        return keyval_pb2.ReadResponse(status=status, key=key, value=self.keyval_store[key]['value'], current_version=self.keyval_store[key]['version'])
    
    def Write(self, request, context):
        key = request.key
        value = request.value
        current_version = request.current_version
        # Check if write proto is invalid
        if key is None or key == '' or value is None or value == '' or current_version == 0:
            error_string = 'Invalid write proto '
            # Find the first valid field in the proto and append to the error string
            if key is not None and key != '':
                error_string += 'key: "%s"\n'%key
            elif value is not None and value != '':
                error_string += 'value: "%s"\n'%value
            elif current_version != 0:
                error_string += 'current_version: %s\n'%current_version

            status = keyval_pb2.Status(server_id=SERVER_ID, ok=False, error=error_string)
            return keyval_pb2.WriteResponse(status=status)
        
        # Blind write
        if current_version < 0:
            self.keyval_store[key] = {'value': value, 'version': 1}
            status = keyval_pb2.Status(server_id=SERVER_ID, ok=True)
            return keyval_pb2.WriteResponse(status=status, key=key, new_version=1)
        
        # Check for erroneous conditions
        # Check if trying to overwrite the value of a key, but the key does not exist
        if key not in self.keyval_store:
            status = keyval_pb2.Status(server_id=SERVER_ID, ok=False, error='Write aborted. Record missing but Write expected value to exist at version %d'%current_version)
            return keyval_pb2.WriteResponse(status=status, key=key, new_version=current_version+1)      
        
        # Check if there is a version mismatch
        if current_version != self.keyval_store[key]['version']:
            status = keyval_pb2.Status(server_id=SERVER_ID, ok=False, error='Write aborted. Record version mismatch. Expected = %d, Actual = %d'%(current_version, self.keyval_store[key]['version']))
            return keyval_pb2.WriteResponse(status=status, key=key, new_version=current_version+1)
        
        # Write Request is valid. Update value and version
        new_version = current_version + 1
        self.keyval_store[key]['version'] = new_version
        self.keyval_store[key]['value'] = value
        status = keyval_pb2.Status(server_id=SERVER_ID, ok=True)
        return keyval_pb2.WriteResponse(status=status, key=key, new_version=new_version)

    def Delete(self, request, context):
        key = request.key
        current_version = request.current_version

        # Check if delete proto is invalid
        if key is None or key == '' or current_version == 0:
            error_string = 'Invalid delete proto '
            # Find the first valid field in the proto and append it to the error string
            if key is not None and key != '':
                error_string += 'key: "%s"\n'%key
            elif current_version != 0:
                error_string += 'current_version: %s\n'%current_version

            status = keyval_pb2.Status(server_id=SERVER_ID, ok=False, error=error_string)
            return keyval_pb2.DeleteResponse(status=status)

        # Check for erroneous conditions
        # Check if trying to delete a key, but the key does not exist
        if key not in self.keyval_store:
            status = keyval_pb2.Status(server_id=SERVER_ID, ok=False, error='Key not present %s'%key)
            return keyval_pb2.DeleteResponse(status=status)

        # Check if there is a version mismatch
        if current_version > 0 and current_version != self.keyval_store[key]['version']:
            status = keyval_pb2.Status(server_id=SERVER_ID, ok=False, error='Delete aborted. Record version mismatch: Expected = %d, Actual = %d'%(current_version, self.keyval_store[key]['version']))
            return keyval_pb2.DeleteResponse(status=status)            
        
        # Delete Request is valid. Delete the key.
        deleted_value = self.keyval_store[key]['value']
        deleted_version = self.keyval_store[key]['version']
        self.keyval_store.pop(key)
        status = keyval_pb2.Status(server_id=SERVER_ID, ok=True)
        return keyval_pb2.DeleteResponse(status=status, key=key, deleted_value=deleted_value, deleted_version=deleted_version)

    def List(self, request, context):
        entries = []
        for key in self.keyval_store:
            entry = keyval_pb2.Entry(key=key, value=self.keyval_store[key]['value'], current_version=self.keyval_store[key]['version'])
            entries.append(entry)
        status = keyval_pb2.Status(server_id=SERVER_ID, ok=True)
        return keyval_pb2.ListResponse(status=status, entries=entries)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    keyval_pb2_grpc.add_KeyValueServicer_to_server(KeyValueServicer(), server)
    SERVICE_NAMES = (
        keyval_pb2.DESCRIPTOR.services_by_name['KeyValue'].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)
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