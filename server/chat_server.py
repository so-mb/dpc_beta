# CHAT SERVER IMPLEMENTATION

import socket
import select
import sys
import json

# Constants
HEADER_LENGTH = 2

# Handle command line arguments
if len(sys.argv) != 2:
    print("Usage: python chat_server.py <port>")
    sys.exit(1)

port = int(sys.argv[1])

# Get the IP address of the server machine
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
print(f"Server IP Address: {local_ip}")

# Create a listener socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((local_ip, port))
server_socket.listen()

# List of sockets to monitor with select
sockets_list = [server_socket]
clients = {}

print(f"Server is listening on {local_ip}:{port}")

# Function to handle receiving data from clients
def receive_data(client_socket):
    try:
        data = client_socket.recv(HEADER_LENGTH)
        if not len(data):
            return False
        data_length = int.from_bytes(data, byteorder='big')
        return client_socket.recv(data_length).decode('utf-8')
    except:
        return False

# Main server loop
while True:
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
    
    for notified_socket in read_sockets:
        if notified_socket == server_socket:
            # Accept new connection
            client_socket, client_address = server_socket.accept()
            user_data = receive_data(client_socket)
            if user_data is False:
                continue
            
            user = json.loads(user_data)['nick']
            sockets_list.append(client_socket)
            clients[client_socket] = user

            # Broadcast join message
            join_message = json.dumps({"type": "join", "nick": user})
            for client in clients.keys():
                if client != client_socket:
                    client.send(len(join_message).to_bytes(HEADER_LENGTH, byteorder='big') + join_message.encode('utf-8'))
            
            print(f"+++ Accepted new connection from {client_address[0]}:{client_address[1]} with username: {user}")

        else:
            message = receive_data(notified_socket)
            if message is False:
                # Client disconnected
                user = clients[notified_socket]
                sockets_list.remove(notified_socket)
                del clients[notified_socket]

                # Broadcast leave message
                leave_message = json.dumps({"type": "leave", "nick": user})
                for client in clients.keys():
                    client.send(len(leave_message).to_bytes(HEADER_LENGTH, byteorder='big') + leave_message.encode('utf-8'))
                
                print(f"--- Closed connection from {notified_socket.getpeername()} with username: {user}")
                continue

            # Broadcast received message to other clients
            user = clients[notified_socket]
            message_data = json.loads(message)
            chat_message = json.dumps({"type": "chat", "nick": user, "message": message_data['message']})
            for client in clients.keys():
                if client != notified_socket:
                    client.send(len(chat_message).to_bytes(HEADER_LENGTH, byteorder='big') + chat_message.encode('utf-8'))

    for notified_socket in exception_sockets:
        sockets_list.remove(notified_socket)
        del clients[notified_socket]
