"""Python implementation of the KeyValue client."""

from __future__ import print_function
import logging
import grpc

import keyval_pb2
import keyval_pb2_grpc


def read_key(stub, key):
    response = stub.Read(keyval_pb2.ReadRequest(key=key))
    return response

def write_key(stub, key, value, version):
    response = stub.Write(keyval_pb2.WriteRequest(key=key, value=value, current_version=version))
    return response

def delete_key(stub, key, version):
    response = stub.Delete(keyval_pb2.DeleteRequest(key=key, current_version=version))
    return response

def run():
  channel = grpc.insecure_channel('localhost:50051')
  stub = keyval_pb2_grpc.KeyValueStub(channel)
  response = write_key(stub, "avjot", "singh", 1)
  print("KeyValue client received: {}, {}".format(response.key, response.new_version))
  response = read_key(stub, "avjot")
  print("KeyValue client received: {}, {}".format(response.key, response.value))

if __name__ == '__main__':
    logging.basicConfig()
    run()
