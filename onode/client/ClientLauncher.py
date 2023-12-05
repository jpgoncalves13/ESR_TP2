from tkinter import Tk
from client.Client import Client
import threading


class ClientLauncher(threading.Thread):

	def __init__(self, neighbour, port, stream_id, ep):
		super().__init__()
		self.stream_id = stream_id
		self.neighbour = neighbour
		self.port = port
		self.ep = ep

	def run(self):
		root = Tk()

		# Create a new client
		app = Client(root, self.neighbour, self.port, self.stream_id, self.ep)
		app.master.title("RTPClient")
		root.mainloop()


