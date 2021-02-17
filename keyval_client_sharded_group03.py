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

def run():
  channel1 = grpc.insecure_channel('localhost:50050')
  channel2 = grpc.insecure_channel('localhost:50051')

  # Try connecting to server 1
  try:
    grpc.channel_ready_future(channel1).result(timeout=10)
  except grpc.FutureTimeoutError:
    sys.exit('Error connecting to server 1')
  else:
    stub1 = keyval_pb2_grpc.KeyValueStub(channel1)
  
  # Try connecting to server 2
  try:
    grpc.channel_ready_future(channel2).result(timeout=10)
  except grpc.FutureTimeoutError:
    sys.exit('Error connecting to server 2')
  else:
    stub2 = keyval_pb2_grpc.KeyValueStub(channel2)

  # Write odd keys to server 1 and even keys to server 2
  for i in range(10):
    if i % 2 == 0:
      # Blind write
      write_key(stub2, "SharedKey0" + str(i), "Value0" + str(i), -1)
    else:
      # Blind write
      write_key(stub1, "SharedKey0" + str(i), "Value0" + str(i), -1)

  # List all entries on server 1
  list_entries(stub1)

  # List all entries on server 2
  list_entries(stub2)

if __name__ == '__main__':
    logging.basicConfig()
    parser = argparse.ArgumentParser(description='KeyVal Client arguments')
    parser.add_argument('--write_timeout', type=float, help='Timeout for the RPC request', default=1)
    args = parser.parse_args()
    TIMEOUT = args.write_timeout

    run()
