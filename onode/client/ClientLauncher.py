from tkinter import Tk
from client.Client import Client
import threading


class ClientLauncher(threading.Thread):

	def __init__(self, ep):
		super().__init__()
		self.ep = ep

	def run(self):
		root = Tk()

		# Create a new client
		app = Client(root, self.ep)
		app.master.title("RTPClient")
		root.mainloop()


