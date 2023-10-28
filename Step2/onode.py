import sys
import bootstraper


def main():
    if len(sys.argv) < 2:
        print('How to use the program: onode.py (--<function> <jsonfile>?)*')
        return

    i = 0
    while i < len(sys.argv):
        match sys.argv[i+1]:
            case '--bootstrapper':
                file_name = sys.argv[i+2]
                i += 2
            case '--server':
                i += 1
            case '--client':
                i += 1
            case '--rendezvous':
                i += 1


if __name__ == '__main__':
    main()
