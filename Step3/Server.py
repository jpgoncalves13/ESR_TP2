import sys, socket
from VideoStream import VideoStream

from ServerWorker import ServerWorker

class Server:	
	
	def main(self):
		clients = {}
		streams = {}
		SERVER_PORT = 5000
		rtspSocket = None
		rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		rtspSocket.bind(('', SERVER_PORT))        
		# Receive client info (address,port) through RTSP/TCP session
		while True:
			data, clientAddress = rtspSocket.recvfrom(256)
   			
			if rtspSocket is not None:
				if clientAddress[0] not in clients:
					clientInfo = {'rtspSocket': rtspSocket, 'clientAddress': clientAddress, 'state': 0}
					clients[clientAddress[0]] = clientInfo
				else: 
					clientInfo = clients[clientAddress[0]]
				print(data)
				ServerWorker(clientInfo, streams, data.decode("utf-8")).run()
    

if __name__ == "__main__":
	(Server()).main()


