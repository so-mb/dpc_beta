# Multiuser Chat Application for Doctors and Patients

This project is a multiuser chat application designed to facilitate secure and efficient communication between healthcare providers and their patients. The application supports multiple user roles (Doctor, Nurse, Patient, Other) and ensures data privacy and security through end-to-end encryption.

## Features

### Old Stable Version (DPC v1 and v2)
See at https://github.com/so-mb/doc_pat_multichat

- **User Authentication and Role Management:** Secure authentication for different user roles.
- **Secure Messaging:** End-to-end encryption for all messages.
- **Appointment Scheduling:** Integrated system for booking appointments.
- **Patient Records:** Secure access and update of patient records by authorized doctors.
- **Notifications:** Appointment reminders, new message alerts, and important updates.
- **Multi-Platform Support:** Compatible with desktops, tablets, and smartphones.
- **Regulatory Compliance:** Adheres to relevant healthcare regulations such as HIPAA and GDPR.

### New Stable Version (DPC v3 and v4)

- **Private Messaging:** Users can send private messages using the `/send_private="<nickname>" <message>` command.
- **File Transfer:**
  - **FHIR Data:** Send FHIR data files using `/send_fhir <file_path>` and `/send_fhir="<nickname>" <file_path>` for private transfers.
  - **Media Files:** Send media files (e.g., .jpg, .jpeg, .png, .gif, .pdf) using `/send_media <file_path>` and `/send_media="<nickname>" <file_path>` for private transfers.
  - **File Size Limit:** A 5MB file size limit is enforced for all transfers.
  - **Validation:** Ensures only .json files for FHIR data and validates JSON format.
- **Help Command:** `/help` command displays a list of available commands.
- **Nickname Handling:**
  - **Uniqueness:** Handles duplicate nicknames by appending a number (e.g., Alice, Alice1, Alice2).
  - **Case Insensitivity:** Commands and nicknames are case-insensitive.
- **Improved UI Handling:** Enhancements in message and file transfer error handling for a better user experience.

## Getting Started

### Prerequisites

- Python 3.x
- A local network (e.g., Wi-Fi) for multiuser functionality

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/so-mb/dpc_beta
   cd dpc_beta
   ```

2. Install the required Python packages:
   ```
   pip install curses fhir.resources cryptography
   ```

### Usage

#### Running the Server

1. Find the local IP address of the machine running the server:
   - **On Windows:**
     ```shell
     ipconfig
     ```
     Look for the "IPv4 Address" under your active network connection.

   - **On macOS/Linux:**
     ```shell
     ifconfig
     ```
     Look for the "inet" address under your active network connection.

2. Run the server script with the desired port number:
   ```shell
   python chat_server.py <port>
   ```
   Example:
   ```shell
   python chat_server.py 12345
   ```
   The server will print its local IP address. Share this address and the port number with your classmates.

#### Running the Client

1. On each client machine, run the client script with the user's nickname, server IP address, and port number:
   ```shell
   python chat_client.py <nickname> <server_ip_address> <port>
   ```
   Example:
   ```shell
   python chat_client.py Alice 192.168.1.100 12345
   ```

### Testing Locally

To test the application on a single machine, you can open multiple terminal windows:

1. **Terminal 1 (Server):**
   ```shell
   python chat_server.py 12345
   ```

2. **Terminal 2 (Client 1):**
   ```shell
   python chat_client.py User1 127.0.0.1 12345
   ```

3. **Terminal 3 (Client 2):**
   ```shell
   python chat_client.py User2 127.0.0.1 12345
   ```

### Project Structure

- `chat_server.py`: Server-side code to handle multiple client connections and message broadcasting.
- `chat_client.py`: Client-side code for user interaction and communication with the server.
- `chatui.py`: Text-based user interface (TUI) management using the `curses` module.
- `fhir_handler.py`: Module for validating FHIR data.
- `README.md`: Project documentation.

### Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

### Acknowledgements

- Thanks to the developers of the `curses` module for providing a robust TUI library.
- Special thanks to the [Beej's Guide to Network Programming](https://beej.us/guide/bgnet/html/) for network programming concepts.
- Gratitude to the FHIR community for providing tools to manage healthcare data efficiently.
- Acknowledgement to the developers of the `cryptography` module for enabling secure encryption.

### Updates

This version of the application includes several enhancements and new features over the previous versions, focusing on private messaging, improved file transfer capabilities, and robust error handling to enhance user experience and application functionality.