import sys, socket

from ServerWorker import ServerWorker

class Server:	
	
	def main(self):
		try:
			#SERVER_IP = sys.argv[1]
			SERVER_PORT = int(sys.argv[1])
		except:
			print("[Usage: Server.py Server_port]\n")
		rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		rtspSocket.bind(('', SERVER_PORT))        
		# Receive client info (address,port) through RTSP/TCP session
		while True:
			clientInfo = {}
			clientInfo['rtspSocket'] = rtspSocket.recvfrom(1024)
			ServerWorker(clientInfo).run()		

if __name__ == "__main__":
	(Server()).main()


