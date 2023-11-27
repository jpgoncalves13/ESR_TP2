import sys
from tkinter import Tk
from Client import Client

if __name__ == "__main__":
	try:
		serverAddr = sys.argv[1]
		stream_id = sys.argv[2]	
	except:
		print("[Usage: ClientLauncher.py Server_name Stream_id]\n")	
	
	root = Tk()
	
	# Create a new client
	app = Client(root, serverAddr, 5000, 5000, stream_id)
	app.master.title("RTPClient")	
	root.mainloop()
	