import socket               # Import socket module

def create_client_transfer(file_path):
    s = socket.socket()         # Create a socket object
    host = socket.gethostname() # Get local machine name
    port = 12345                 # Reserve a port for your service.

    s.connect((host, port))
    f = open(str(file_path),'rb')
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
    s.close()