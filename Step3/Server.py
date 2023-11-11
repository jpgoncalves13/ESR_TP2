import sys, socket

from ServerWorker import ServerWorker

class Server:	
	
	def main(self):
		try:
			#SERVER_IP = sys.argv[1]
			SERVER_PORT = int(sys.argv[1])
		except:
			print("[Usage: Server.py Server_port]\n")
		rtspSocket = None
		rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		rtspSocket.bind(('', SERVER_PORT))        
		# Receive client info (address,port) through RTSP/TCP session
		while True:
			data, clientAddress = rtspSocket.recvfrom(256)
			if rtspSocket is not None:
				clientInfo = {'rtspSocket': rtspSocket, 'clientAddress': clientAddress}
				ServerWorker(clientInfo, data.decode("utf-8")).run()

if __name__ == "__main__":
	(Server()).main()


