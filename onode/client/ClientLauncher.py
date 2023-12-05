from tkinter import Tk
from client.Client import Client
import threading


class ClientLauncher(threading.Thread):

	def __init__(self, neighbour, stream_id, ep):
		super().__init__()
		self.stream_id = stream_id
		self.neighbour = neighbour
		self.ep = ep

	def run(self):
		root = Tk()

		# Create a new client
		app = Client(root, self.neighbour, 5000, 5001, self.stream_id, self.ep)
		app.master.title("RTPClient")
		root.mainloop()


