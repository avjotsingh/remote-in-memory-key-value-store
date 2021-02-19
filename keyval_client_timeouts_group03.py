"""Python implementation of the KeyValue client with timeout experiments"""

from __future__ import print_function
import logging
import grpc
import argparse
import time
import sys

import keyval_pb2
import keyval_pb2_grpc


def read_key(stub, key):
  """
  Helper function to read a key from a server
  Arguments:
    stub- The client stub that communicates with the desired server
    key- The key to be read
  """
  try:
    response = stub.Read(keyval_pb2.ReadRequest(key=key))
    print("Read Result:")
    print_response(response)
  except grpc.RpcError as exception:
    print_response(exception)

def write_key(stub, key, value, version):
  """
  Helper function to write a key-value pair to a server
  Arguments:
    stub- The client stub that communicates with the desired server 
    key- The key to write to the server
    value- The value corresponding to the key
    version- The version number of the key-value pair (-1 for blank write)
  """
  try:
    # Make a write RPC call with a timeout
    response = stub.Write(keyval_pb2.WriteRequest(key=key, value=value, current_version=version), timeout=TIMEOUT)
    print("Write Result:")
    print_response(response)
  except grpc.RpcError as exception:
    print_response(exception)

def delete_key(stub, key, version):
  """
  Helper function to delete a key-value pair from a server
  Arguments:
    stub- The client stub that communicates with the desired server 
    key- The key to delete from the server
    version- The version number of the key-value pair (-1 for blank delete)
  """
  try:
    response = stub.Delete(keyval_pb2.DeleteRequest(key=key, current_version=version))
    print("Delete Result:")
    print_response(response)
  except grpc.RpcError as exception:
    print_response(exception)

def list_entries(stub):
  """
  Helper function to list all the key-value pairs stored on a server
  Arguments:
    stub- The client stub that communicates with the desired server 
  """
  try:
    response = stub.List(keyval_pb2.ListRequest())
    print("List Result:")
    print_response(response)
  except grpc.RpcError as exception:
    print_response(exception)

def print_response(response):
  """
  Helper function to print grpc reponses and exceptions.
  Separates the outputs with a dashed line.
  """
  print(response)
  print("-"*30)

def experiment1_part1(stub):
  """
  Experminet 1 (part 1)
  - Send 5 RPCs to the server with a timeout of 0.5 second
  - Sleep for 5 seconds
  - Send a List RPC
  - Send 5 RPCs at the end to blindly delete all 5 keys
  """

  # Define the keys value pairs to write
  keys = ["Key" + str(i) for i in range(5)]
  values = ["Value" + str(i) for i in range(5)]

  # Send five blind write RPCs to the server with 'Key<i>' where i ranges from 0 to 4
  for i in range(5):
    write_key(stub, keys[i], values[i], -1)

  # Sleep for 5 seconds
  time.sleep(5)

  # List RPC
  list_entries(stub)

  # Blind delete all the keys
  for key in keys:
    delete_key(stub, key, -1)

def experiment1_part2(stub):
  """
  Experminet 1 (part 2)
  - Send 5 RPCs to the server with a timeout of 1.5 seconds
  - Send a List RPC
  - Send 5 RPCs at the end to blindly delete all 5 keys
  """

  # Define the keys value pairs to write
  keys = ["Key" + str(i) for i in range(5)]
  values = ["Value" + str(i) for i in range(5)]

  # Send five blind write RPCs to the server with 'Key<i>' where i ranges from 0 to 4
  for i in range(5):
    write_key(stub, keys[i], values[i], -1)

  # List RPC
  list_entries(stub)

  # Blind delete all the keys
  for key in keys:
    delete_key(stub, key, -1)

def experiment2(stub):
  """
  Experiment 2
  - Write Key1, Value1, current_version = -1
  - Delete Key1, current_version = -1
  - Sleep 1 second
  - List
  """

  # Blind write
  write_key(stub, "Key1", "Value1", -1)

  # Blind delete
  delete_key(stub, "Key1", -1)

  # Sleep for 1 second
  time.sleep(1)

  # List all keys
  list_entries(stub)


if __name__ == '__main__':
  # Parse the command line arguments  
  logging.basicConfig()
  parser = argparse.ArgumentParser(description='KeyVal Client arguments')
  parser.add_argument('--write_timeout', type=float, help='Timeout for the RPC request', default=None)
  args = parser.parse_args()
  # Timeout for Write RPC calls
  TIMEOUT = args.write_timeout

  # Try connecting to the server running at port 50050
  channel = grpc.insecure_channel('localhost:50050')
  try:
    grpc.channel_ready_future(channel).result(timeout=10)
  except grpc.FutureTimeoutError:
    sys.exit('Error connecting to server')
  else:
    stub = keyval_pb2_grpc.KeyValueStub(channel)

  # experiment1_part1(stub)
  # experiment1_part2(stub)
  experiment2(stub)
