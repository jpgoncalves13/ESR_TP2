import sys
from bootstraper import Bootstrapper
from server import Server
from client import Client
from threading import Thread

def main():
    if len(sys.argv) == 2 and sys.argv[1] == '--help':
        info = """
            How to use: onode.py --debug? function* 
            
            function : --bootstrapper <file>
                       --server <file>+ 
                       --client  (Client will have a input to request and cancel the streaming service)
                       --rendezvous 
        """
        print(info)
        return

    debug = False
    bootstrapper = None
    is_rendezvous_point = False
    is_client = False
    server_files = []
    i = 1
    while i < len(sys.argv):
        match sys.argv[i]:
            case '--bootstrapper':
                file_name = sys.argv[i+1]
                bootstrapper = Bootstrapper(file_name, debug)
                i += 2
            case '--server':
                i += 1
                while i < len(sys.argv) and sys.argv[i] not in ('--client', '--rendezvous', '--debug', '--bootstrapper'):
                    server_files.append(sys.argv[i])
                    i += 1
            case '--client':
                is_client = True
                i += 1
            case '--rendezvous':
                is_rendezvous_point = True
                i += 1
            case '--debug':
                debug = True
                i += 1

    if is_client:
        Client().run()
        

    if not is_client:
        port = 5001
    else:
        port = 5000
    
    server = Server('127.0.0.1', port)
    server.run((debug, bootstrapper, is_rendezvous_point))


if __name__ == '__main__':
    main()
