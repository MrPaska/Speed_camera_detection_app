import cv2
import socket
import pickle
from OpenSSL import SSL
import play_voice
from snackbar import alert_window

packet_size = 65535  # Read 65 KB of data

# Creates a new DTLS context using OpenSSL. This is required to establish a DTLS secure connection.
dtls_context = SSL.Context(SSL.DTLS_METHOD)
# Sets the set of encryption algorithms for the DTLS context. What algos we gonna ues
dtls_context.set_cipher_list(b"HIGH:!aNULL:!eNULL:!PSK:!SRP:!MD5:!RC4:!3DES")
# High-strength encryption algorithms are used, # refers to anonymous ciphers that do not provide authentication, # refers to ciphers that do not perform encryption, # means that ciphers that use pre-negotiated keys will be rejected
# Creates a new UDP socket. socket.AF_INET indicates that an IPv4 address will be used and socket.SOCK_DGRAM indicates that the socket is of UDP type
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Sets the socket's send buffer size to the previously set buffer_size value.
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, packet_size)
# Creates a DTLS connection object wrapping client_socket with dtls_context. This means that all data sent over this socket will be encoded using DTLS.
dtls_client_socket = SSL.Connection(dtls_context, client_socket)

#HOST = "192.168.1.194"
HOST = "34.116.236.252"
PORT = 9090
server_address = (HOST, PORT)

def ping_server():
    try:
        test_msg = b"ping"
        dtls_client_socket.sendto(test_msg, server_address)
        dtls_client_socket.settimeout(3)
        try:
            response, _ = dtls_client_socket.recvfrom(packet_size)  # Max buffer size of data receive
            return response == test_msg
        except socket.timeout as t:
            print(f"Can't conn to server {t}")
            return False
    except Exception as e:
        print(f"Can't conn to server {e}")
        return False


def frames(server, frame, user_id, bounding_box):
    if server:
        # Compressing and to bytes then sending to server
        result, frame_compress = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85]) # Compressing a frame into a JPEG image.
        data_tuple = (frame_compress, user_id, bounding_box)
        byte_data = pickle.dumps(data_tuple)  # Converting to a byte stream
        dtls_client_socket.sendto(byte_data, server_address)

        try:
            packet = dtls_client_socket.recvfrom(packet_size)
            data = packet[0]
            data = pickle.loads(data)
            if data[0] == "momentinis":
                return data[0]
            elif data[0] == "vidutinis":
                return data[0], data[1]
            else:
                return "No"
        except Exception as e:
            pass
    else:
        print("Socket closed")
        dtls_client_socket.close()
        client_socket.close()
