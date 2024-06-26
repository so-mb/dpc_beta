# CHAT CLIENT IMPLEMENTATION

import socket
import threading
import sys
import json
import os
import re
from chatui import init_windows, read_command, print_message, end_windows
from fhir.resources.patient import Patient # type: ignore
from pydantic import ValidationError # type: ignore
from cryptography.fernet import Fernet # type: ignore

# Constants
HEADER_LENGTH = 4
CATEGORIES = ["Doctor", "Nurse", "Patient", "Other"]
MEDIA_TYPES = ['.jpg', '.jpeg', '.png', '.gif', '.pdf']
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

# Encryption key (for demonstration, in practice would handle this more securely)
ENCRYPTION_KEY = Fernet.generate_key()
cipher_suite = Fernet(ENCRYPTION_KEY)

# Handle command line arguments
if len(sys.argv) != 4:
    print("Usage: python chat_client.py <nickname> <server_address> <port>")
    sys.exit(1)

nickname = sys.argv[1]
server_address = sys.argv[2]
port = int(sys.argv[3])

# Initialize TUI
init_windows()

# Function to get user category
def get_user_category():
    print_message("*** Please select your category: 1. Doctor, 2. Nurse, 3. Patient, 4. Other", f"{nickname}> ")
    while True:
        category_choice = read_command("Enter the number of your category: ")
        if category_choice in ["1", "2", "3", "4"]:
            return CATEGORIES[int(category_choice) - 1]
        print_message("*** Invalid choice. Please select a valid category.", f"{nickname}> ")

# Get user category
category = get_user_category()
nickname_with_category = f"{nickname} ({category})"

# Create a socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((server_address, port))

# Send initial "hello" packet
hello_packet = json.dumps({"type": "hello", "nick": nickname, "category": category, "encryption_key": ENCRYPTION_KEY.decode()})
client_socket.send(len(hello_packet).to_bytes(HEADER_LENGTH, byteorder='big') + hello_packet.encode('utf-8'))

# Function to receive messages from the server
def receive_messages():
    global nickname_with_category
    while True:
        try:
            data_length = int.from_bytes(client_socket.recv(HEADER_LENGTH), byteorder='big')
            data = client_socket.recv(data_length).decode('utf-8')
            message = json.loads(data)

            if message['type'] == 'chat':
                if message['nick'] == nickname_with_category:
                    print_message(f"Me: {message['message']}")
                else:
                    print_message(f"{message['nick']}: {message['message']}")
            elif message['type'] == 'private':
                print_message(f"*** Private message from {message['nick']}: {message['message']}", f"{nickname_with_category}> ")
            elif message['type'] == 'join':
                print_message(f"*** {message['nick']} has joined the chat")
            elif message['type'] == 'leave':
                print_message(f"*** {message['nick']} has left the chat")
            elif message['type'] == 'fhir':
                print_message(f"*** Received FHIR data from {message['nick']}. View the data at: {message['data']}", f"{nickname_with_category}> ")
            elif message['type'] == 'media':
                print_message(f"*** Received media from {message['nick']}. View the file at: {message['data']}", f"{nickname_with_category}> ")
            elif message['type'] == 'error':
                print_message(f"*** Error: {message['message']}", f"{nickname_with_category}> ")
            elif message['type'] == 'update_nick':
                nickname_with_category = message['nick']
        except Exception as e:
            print_message(f"*** Connection to server lost: {e}")
            break

# Function to send FHIR data to the server
def send_fhir_data(filepath, target_nick=None):
    if not filepath.endswith('.json'):
        print_message("*** Only JSON FHIR data is accepted", f"{nickname}> ")
        return

    if not os.path.isfile(filepath):
        print_message("*** File does not exist", f"{nickname}> ")
        return

    if os.path.getsize(filepath) > MAX_FILE_SIZE:
        print_message("*** File size exceeds the 5MB limit", f"{nickname}> ")
        return

    try:
        with open(filepath, 'r') as file:
            try:
                fhir_json = file.read()
                json.loads(fhir_json)  # Check if JSON is correctly formed
            except json.JSONDecodeError:
                print_message("*** Incorrectly formed JSON file", f"{nickname}> ")
                return

        # Validate FHIR data
        try:
            patient = Patient.parse_raw(fhir_json)
        except ValidationError as ve:
            handle_long_message("*** Invalid FHIR Data", f"{nickname}> ")
            handle_long_message(str(ve), f"{nickname}> ")
            return
        except Exception as e:
            handle_long_message("*** Invalid FHIR Data", f"{nickname}> ")
            handle_long_message(str(e), f"{nickname}> ")
            return

        encrypted_fhir = cipher_suite.encrypt(fhir_json.encode())
        fhir_packet = json.dumps({"type": "fhir", "data": encrypted_fhir.decode(), "target": target_nick})
        client_socket.send(len(fhir_packet).to_bytes(HEADER_LENGTH, byteorder='big') + fhir_packet.encode('utf-8'))
        if target_nick:
            print_message(f"*** FHIR data sent to {target_nick} successfully", f"{nickname}> ")
        else:
            print_message("*** FHIR data sent successfully", f"{nickname}> ")
    except Exception as e:
        handle_long_message("*** Error sending FHIR data", f"{nickname}> ")
        handle_long_message(str(e), f"{nickname}> ")

# Function to send media files to the server
def send_media(filepath, target_nick=None):
    if not any(filepath.lower().endswith(ext) for ext in MEDIA_TYPES):
        print_message("*** Only media files (.jpg, .jpeg, .png, .gif, .pdf) are accepted", f"{nickname}> ")
        return

    if not os.path.isfile(filepath):
        print_message("*** File does not exist", f"{nickname}> ")
        return

    if os.path.getsize(filepath) > MAX_FILE_SIZE:
        print_message("*** File size exceeds the 5MB limit", f"{nickname}> ")
        return

    try:
        with open(filepath, 'rb') as file:
            media_data = file.read()

        encrypted_media = cipher_suite.encrypt(media_data)
        media_packet = json.dumps({"type": "media", "filename": os.path.basename(filepath), "data": encrypted_media.decode('latin1'), "target": target_nick})
        client_socket.send(len(media_packet).to_bytes(HEADER_LENGTH, byteorder='big') + media_packet.encode('utf-8'))
        if target_nick:
            print_message(f"*** Media file sent to {target_nick} successfully", f"{nickname}> ")
        else:
            print_message("*** Media file sent successfully", f"{nickname}> ")
    except Exception as e:
        handle_long_message("*** Error sending media file", f"{nickname}> ")
        handle_long_message(str(e), f"{nickname}> ")

# Function to display help
def display_help():
    help_message = """
Available commands:
  /send_fhir <file_path>         : Send FHIR data as a JSON file.
  /send_fhir="<nickname>" <file_path> : Send FHIR data to a specific user.
  /send_media <file_path>        : Send media files (e.g., .jpg, .jpeg, .png, .gif, .pdf).
  /send_media="<nickname>" <file_path> : Send media file to a specific user.
  /send_private="<nickname>" <msg> : Send a private message to a specific user.
  /quit                          : Quit the chat.
  /help                          : Display this help message.
"""
    handle_long_message(help_message, f"{nickname}> ")

# Function to send messages to the server
def send_message():
    print_message(f"*** Welcome to the DP Chat. Remember to chat responsibly. You are chatting as << {nickname_with_category} >>", f"{nickname_with_category}> ")
    while True:
        message = read_command(f"Me> ")
        if message.strip() == "":
            continue
        if message == "/quit" or message == "/QUIT":
            confirmation = read_command("Are you sure you want to quit? [Yes or y / No or n (default)] ")
            if confirmation.lower() in ["yes", "y"]:
                print("*** Quitting chat")
                break
            else:
                print_message("*** DP Chat says 'Quit cancelled.'", f"{nickname}> ")
                continue
        elif message == "/help":
            display_help()
            continue
        elif message.startswith("/send_fhir="):
            match = re.match(r'/send_fhir=["\'](.+?)["\'] (.+)', message)
            if not match:
                print_message("*** Invalid FHIR send format. Use /send_fhir=\"<nickname>\" <file_path>", f"{nickname}> ")
                continue
            target_nick = match.group(1)
            filepath = match.group(2)
            send_fhir_data(filepath, target_nick)
            continue
        elif message.startswith("/send_fhir "):
            filepath = message.split(" ", 1)[1]
            send_fhir_data(filepath)
            continue
        elif message.startswith("/send_media="):
            match = re.match(r'/send_media=["\'](.+?)["\'] (.+)', message)
            if not match:
                print_message("*** Invalid media send format. Use /send_media=\"<nickname>\" <file_path>", f"{nickname}> ")
                continue
            target_nick = match.group(1)
            filepath = match.group(2)
            send_media(filepath, target_nick)
            continue
        elif message.startswith("/send_media "):
            filepath = message.split(" ", 1)[1]
            send_media(filepath)
            continue
        elif message.startswith("/send_private="):
            match = re.match(r'/send_private=["\'](.+?)["\'] (.+)', message)
            if not match:
                print_message("*** Invalid private message format. Use /send_private=\"<nickname>\" <message>", f"{nickname}> ")
                continue
            target_nick = match.group(1)
            private_message = match.group(2)
            private_packet = json.dumps({"type": "private", "target": target_nick, "message": private_message})
            client_socket.send(len(private_packet).to_bytes(HEADER_LENGTH, byteorder='big') + private_packet.encode('utf-8'))
            print_message(f"Me to {target_nick}: {private_message}")
            continue

        chat_packet = json.dumps({"type": "chat", "message": message})
        client_socket.send(len(chat_packet).to_bytes(HEADER_LENGTH, byteorder='big') + chat_packet.encode('utf-8'))
        # Show the message in the sender's terminal as "Me"
        print_message(f"Me: {message}")

    client_socket.close()
    end_windows()
    sys.exit(0)

def handle_long_message(message, prompt):
    max_width = 80  # Adjust based on your terminal's width
    lines = split_message_to_lines(message, max_width)
    for line in lines:
        print_message(line, prompt)

def split_message_to_lines(message, max_width):
    words = message.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 > max_width:
            lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word) + 1
        else:
            current_line.append(word)
            current_length += len(word) + 1

    if current_line:
        lines.append(' '.join(current_line))

    return lines

# Start the receiving thread
receive_thread = threading.Thread(target=receive_messages)
receive_thread.daemon = True
receive_thread.start()

# Start the sending thread
send_message()
