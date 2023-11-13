import sys
from tkinter import Tk
from ProgEx.Python.ClienteGUI import ClienteGUI

if __name__ == "__main__":
	try:
		addr = '10.0.0.21'
		port = 25000
	except:
		print("[Usage: Cliente.py]\n")	
	
	root = Tk()
	
	# Create a new client
	app = ClienteGUI(root, addr, port)
	app.master.title("Cliente Exemplo")	
	root.mainloop()
	
