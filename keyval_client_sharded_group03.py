"""Python implementation of the KeyValue client that stores key-value pairs across shards."""

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
    print("Read result:")
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
    response = stub.Write(keyval_pb2.WriteRequest(key=key, value=value, current_version=version))
    print("Write result:")
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
    print("Delete result:")
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
    print("List result:")
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

def run():
  """
  Driver function to write key-value pairs on two shards.
  """

  # Channel for server 1
  channel1 = grpc.insecure_channel('localhost:50050')
  # Channel for server 2
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
      write_key(stub2, "ShardKey" + str(i), "Value" + str(i), -1)
    else:
      # Blind write
      write_key(stub1, "ShardKey" + str(i), "Value" + str(i), -1)

  # List all entries on server 1
  list_entries(stub1)

  # List all entries on server 2
  list_entries(stub2)

if __name__ == '__main__':
    # Invoke the driver function
    run()
