import logging

import grpc
import sys
import helloworld_pb2
import helloworld_pb2_grpc
import psycopg2
from psycopg2.extras import LogicalReplicationConnection

def run(msg_str):
    mongourl = sys.argv[1]
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = helloworld_pb2_grpc.GreeterStub(channel)
        response = stub.SayHello(helloworld_pb2.HelloRequest(name = msg_str, url = mongourl))
    print("Greeter client received: " + response.message)

def consume(msg):
    msg_str = str(msg.payload)
    run(msg_str)

if __name__ == '__main__':
    logging.basicConfig()
    my_connection  = psycopg2.connect(
                   "dbname='test' host='127.0.0.1' user='postgres' password='12345'" ,
                   connection_factory = LogicalReplicationConnection)
    cur = my_connection.cursor()
    replication_slot_name = 'testing_slot1'
    try:
        cur.drop_replication_slot(replication_slot_name)  
        cur.create_replication_slot(replication_slot_name, output_plugin = 'wal2json')
    except:
        cur.create_replication_slot(replication_slot_name, output_plugin = 'wal2json')
    cur.start_replication(slot_name = replication_slot_name, options = {'pretty-print' : 1}, decode= True)
    cur.consume_stream(consume)