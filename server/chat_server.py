# CHAT SERVER IMPLEMENTATION

import socket
import select
import sys
import json
import os
import uuid
from http.server import SimpleHTTPRequestHandler, HTTPServer
import threading
from fhir_handler import validate_fhir_data
from cryptography.fernet import Fernet

# Constants
HEADER_LENGTH = 4

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
encryption_keys = {}
nicknames = {}

# Directory to store FHIR JSON files
FHIR_FILES_DIR = "../fhir_files/"
MEDIA_FILES_DIR = "../media_files/"
os.makedirs(FHIR_FILES_DIR, exist_ok=True)
os.makedirs(MEDIA_FILES_DIR, exist_ok=True)

print(f"Server is listening on {local_ip}:{port}")

def save_file(data, filename, dir):
    filepath = os.path.join(dir, filename)
    with open(filepath, 'wb') as f:
        f.write(data)
    return filename

class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Remove the leading /
        path = path.lstrip('/')
        
        if path.startswith('fhir_files/'):
            return os.path.join(FHIR_FILES_DIR, path[len('fhir_files/'):])
        elif path.startswith('media_files/'):
            return os.path.join(MEDIA_FILES_DIR, path[len('media_files/'):])
        else:
            return SimpleHTTPRequestHandler.translate_path(self, path)

def start_http_server():
    handler = CustomHTTPRequestHandler
    httpd = HTTPServer(('localhost', 8000), handler)
    httpd.serve_forever()

http_server_thread = threading.Thread(target=start_http_server)
http_server_thread.daemon = True
http_server_thread.start()

def get_unique_nickname(nick, category):
    base_nick = f"{nick} ({category})"
    unique_nick = base_nick
    count = 1
    while unique_nick.lower() in (name.lower() for name in clients.values()):
        unique_nick = f"{base_nick}{count}"
        count += 1
    return unique_nick

# Function to handle receiving data from clients
def receive_data(client_socket):
    try:
        data = client_socket.recv(HEADER_LENGTH)
        if not len(data):
            return False
        data_length = int.from_bytes(data, byteorder='big')
        data = b""
        while len(data) < data_length:
            packet = client_socket.recv(data_length - len(data))
            if not packet:
                return False
            data += packet
        return data.decode('utf-8')
    except Exception as e:
        print(f"Error receiving data: {e}")
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
            
            user_info = json.loads(user_data)
            nick = user_info['nick']
            category = user_info['category']
            unique_nick = get_unique_nickname(nick, category)
            nicknames[client_socket] = unique_nick
            encryption_key = user_info['encryption_key'].encode()
            encryption_keys[client_socket] = encryption_key
            cipher_suite = Fernet(encryption_key)
            sockets_list.append(client_socket)
            clients[client_socket] = unique_nick

            # Inform the client of their unique nickname
            update_nick_message = json.dumps({"type": "update_nick", "nick": unique_nick})
            client_socket.send(len(update_nick_message).to_bytes(HEADER_LENGTH, byteorder='big') + update_nick_message.encode('utf-8'))

            # Broadcast join message
            join_message = json.dumps({"type": "join", "nick": unique_nick})
            for client in clients.keys():
                if client != client_socket:
                    client.send(len(join_message).to_bytes(HEADER_LENGTH, byteorder='big') + join_message.encode('utf-8'))
            
            print(f"+++ Accepted new connection from {client_address[0]}:{client_address[1]} with username: {unique_nick}")

        else:
            message = receive_data(notified_socket)
            if message is False:
                # Client disconnected
                user = clients[notified_socket]
                sockets_list.remove(notified_socket)
                del clients[notified_socket]
                del encryption_keys[notified_socket]
                del nicknames[notified_socket]

                # Broadcast leave message
                leave_message = json.dumps({"type": "leave", "nick": user})
                for client in clients.keys():
                    client.send(len(leave_message).to_bytes(HEADER_LENGTH, byteorder='big') + leave_message.encode('utf-8'))
                
                print(f"--- Closed connection from {notified_socket.getpeername()} with username: {user}")
                continue

            # Process received message
            user = clients[notified_socket]
            message_data = json.loads(message)
            cipher_suite = Fernet(encryption_keys[notified_socket])

            if message_data['type'] == 'fhir':
                decrypted_fhir = cipher_suite.decrypt(message_data['data'].encode())
                is_valid, validation_message = validate_fhir_data(decrypted_fhir.decode())
                if is_valid:
                    filename = save_file(decrypted_fhir, f"{uuid.uuid4()}.json", FHIR_FILES_DIR)
                    file_url = f"http://localhost:8000/fhir_files/{filename}"
                    fhir_message = json.dumps({"type": "fhir", "nick": user, "data": file_url})
                    for client in clients.keys():
                        if client != notified_socket:
                            client.send(len(fhir_message).to_bytes(HEADER_LENGTH, byteorder='big') + fhir_message.encode('utf-8'))
                else:
                    error_message = json.dumps({"type": "error", "message": validation_message})
                    notified_socket.send(len(error_message).to_bytes(HEADER_LENGTH, byteorder='big') + error_message.encode('utf-8'))
            elif message_data['type'] == 'media':
                decrypted_media = cipher_suite.decrypt(message_data['data'].encode('latin1'))
                filename = save_file(decrypted_media, message_data['filename'], MEDIA_FILES_DIR)
                file_url = f"http://localhost:8000/media_files/{filename}"
                media_message = json.dumps({"type": "media", "nick": user, "data": file_url})
                for client in clients.keys():
                    if client != notified_socket:
                        client.send(len(media_message).to_bytes(HEADER_LENGTH, byteorder='big') + media_message.encode('utf-8'))
            elif message_data['type'] == 'private':
                target_nick = message_data['target']
                private_message = message_data['message']
                found = False
                for client_socket, nickname in clients.items():
                    if nickname.lower() == target_nick.lower():
                        private_packet = json.dumps({"type": "private", "nick": user, "message": private_message})
                        client_socket.send(len(private_packet).to_bytes(HEADER_LENGTH, byteorder='big') + private_packet.encode('utf-8'))
                        found = True
                        break
                if not found:
                    error_message = json.dumps({"type": "error", "message": f"User '{target_nick}' not found"})
                    notified_socket.send(len(error_message).to_bytes(HEADER_LENGTH, byteorder='big') + error_message.encode('utf-8'))
            else:
                chat_message = json.dumps({"type": "chat", "nick": user, "message": message_data['message']})
                for client in clients.keys():
                    if client != notified_socket:
                        client.send(len(chat_message).to_bytes(HEADER_LENGTH, byteorder='big') + chat_message.encode('utf-8'))

    for notified_socket in exception_sockets:
        sockets_list.remove(notified_socket)
        del clients[notified_socket]
        del encryption_keys[notified_socket]
        del nicknames[notified_socket]
