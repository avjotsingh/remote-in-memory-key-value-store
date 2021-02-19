"""Python implementation of the KeyValue client."""

from __future__ import print_function
import logging
import grpc
import argparse
import time
import sys

import keyval_pb2
import keyval_pb2_grpc


def read_key(stub, key):
  response = stub.Read(keyval_pb2.ReadRequest(key=key))
  print("Read Result:")
  print_response(response)

def write_key(stub, key, value, version):
  try:
    response = stub.Write(keyval_pb2.WriteRequest(key=key, value=value, current_version=version), timeout=TIMEOUT)
    print("Write Result:")
    print_response(response)
  except grpc.RpcError as exception:
    print(exception)

def delete_key(stub, key, version):
  response = stub.Delete(keyval_pb2.DeleteRequest(key=key, current_version=version))
  print("Delete Result:")
  print_response(response)

def list_entries(stub):  
  response = stub.List(keyval_pb2.ListRequest())
  print("List Result:")
  print_response(response)

def print_response(response):
  print(response)
  print("-"*30)

def run(stub):
  channel = grpc.insecure_channel('localhost:50050')
  try:
    grpc.channel_ready_future(channel).result(timeout=10)
  except grpc.FutureTimeoutError:
    sys.exit('Error connecting to server')
  else:
    stub = keyval_pb2_grpc.KeyValueStub(channel)

  # Blind write
  write_key(stub, "Key1", "Value1", -1)
  # Normal write
  write_key(stub, "Key1", "Value2", 1)
  # Version check failure
  write_key(stub, "Key1", "Value3", 1)
  # Version failure with key missing
  write_key(stub, "Key2", "Value3", 1)

  # Normal read
  read_key(stub, "Key1")
  # Non-existing key read
  read_key(stub, "Key2")

  # List
  list_entries(stub)

  # Blind Write
  write_key(stub, "Key3", "Value3", -1)
  # List
  list_entries(stub)

  # Delete with version check failure
  delete_key(stub, "Key1", 1)
  # Normal delete
  delete_key(stub, "Key1", 2)
  # Deletion of non-existent key
  delete_key(stub, "Key1", 2)
  # Delete
  delete_key(stub, "Key3", 1)

  # List
  list_entries(stub)


if __name__ == '__main__':
    logging.basicConfig()
    parser = argparse.ArgumentParser(description='KeyVal Client arguments')
    parser.add_argument('--write_timeout', type=float, help='Timeout for the RPC request', default=1)
    args = parser.parse_args()
    TIMEOUT = args.write_timeout


    run()
