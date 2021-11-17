from concurrent import futures
import logging

import sys
import grpc
import pymongo
import json
import helloworld_pb2
import helloworld_pb2_grpc


class Greeter(helloworld_pb2_grpc.GreeterServicer):
    def SayHello(self, request, context):
        json_object = json.loads(request.name)
        n = len(json_object["change"])
        
        def parseInsertJson(json_obj):
            res = [dict() for i in range(n)]
            columns = [[] for _ in range(n)]
            values= [[] for _ in range(n)]
            for i in range(n):
                columns[i] = json_obj["change"][i]["columnnames"]
                values[i] = json_obj["change"][i]["columnvalues"]
                for col, val in zip(columns[i], values[i]):
                    res[i][col] = val
            return res
        
        def parseUpdateJson(json_obj):
            res = [dict() for i in range(n)]
            old_keys = [[] for _ in range(n)]
            columns = [[] for _ in range(n)]
            values = [[] for _ in range(n)]
            for i in range(n):
                columns[i] = json_obj["change"][i]["columnnames"]
                values[i] = json_obj["change"][i]["columnvalues"]
                for col, val in zip(columns[i], values[i]):
                    res[i][col] = val
                old_keys[i] = json_obj["change"][i]["oldkeys"]["keyvalues"][0]
            return (res, old_keys)
        
        def parseDeleteJson(json_obj):
            old_keys = [[] for _ in range(n)]
            for i in range(n):
                old_keys[i] = json_obj["change"][i]["oldkeys"]["keyvalues"][0]
            return old_keys

        cmd_type = json_object["change"][0]["kind"]  
        if cmd_type == "insert":
            insert_data = parseInsertJson(json_object)
        elif cmd_type == "update":
            update_data, old_keys_data = parseUpdateJson(json_object)
        elif cmd_type == "delete":
            old_keys_data = parseDeleteJson(json_object)
        def get_database():
            # Provide the mongodb atlas url to connect python to mongodb using pymongo
            CONNECTION_STRING = request.url
            #CONNECTION_STRING = "mongodb+srv://yuchelin:cmpe273assignment1@cluster1.sinps.mongodb.net/college?retryWrites=true&w=majority"
        
            # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
            # client = pymongo.MongoClient("localhost", 27017)  # connect Mongo on local
            client = pymongo.MongoClient(CONNECTION_STRING)

            # Create the database for our example (we will use the same database throughout the tutorial
            return client['college']
        dbname = get_database()  # db = college
        collection_name = dbname["students"]   # collection = students
        
        for i in range(n):
            if cmd_type == "insert":
                collection_name.insert_one(insert_data[i])
            elif cmd_type == "update":
                filter = { 'id': old_keys_data[i]}
                new_values = { "$set": update_data[i]} 
                collection_name.update_one(filter, new_values)
            elif cmd_type == "delete":
                collection_name.delete_one({'id' : old_keys_data[i]})
        
        return helloworld_pb2.HelloReply(message='Hello, %s' % request.name)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    helloworld_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
    server.add_insecure_port('[::]:50051')
    print("Greeter is running at port 50051")
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()