import sys
from tkinter import Tk
from Client import Client

if __name__ == "__main__":
	try:
		serverAddr = sys.argv[1]
		fileName = sys.argv[2]	
	except:
		print("[Usage: ClientLauncher.py Server_name Video_file]\n")	
	
	root = Tk()
	
	# Create a new client
	app = Client(root, serverAddr, 5000, 5001, fileName)
	app.master.title("RTPClient")	
	root.mainloop()
	