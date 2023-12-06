import io
import os
import socket
import threading
import tkinter.messagebox as messagebox
from tkinter import *

from PIL import Image, ImageTk, ImageFile

from client.RtpPacket import RtpPacket
from server.stream_packet import Packet, PacketType

ImageFile.LOAD_TRUNCATED_IMAGES = True


class Client:
    def __init__(self, master, ep):
        self.label = None
        self.teardown = None
        self.pause = None
        self.start = None
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.create_widgets()
        self.frameNbr = 0
        self.ep = ep

    def create_widgets(self):
        """Build GUI."""
        # Create Play button
        self.start = Button(self.master, width=20, padx=3, pady=3)
        self.start["text"] = "Play"
        self.start["command"] = self.play_movie
        self.start.grid(row=1, column=1, padx=2, pady=2)

        # Create Pause button
        self.pause = Button(self.master, width=20, padx=3, pady=3)
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pause_movie
        self.pause.grid(row=1, column=2, padx=2, pady=2)

        # Create Teardown button
        self.teardown = Button(self.master, width=20, padx=3, pady=3)
        self.teardown["text"] = "Teardown"
        self.teardown["command"] = self.exit_client
        self.teardown.grid(row=1, column=3, padx=2, pady=2)

        # Create a label to display the movie
        self.label = Label(self.master, height=19)
        self.label.grid(row=0, column=0, columnspan=4, sticky=W + E + N + S, padx=5, pady=5)

    def exit_client(self):
        """Teardown button handler."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        packet = Packet(PacketType.LEAVE, '0.0.0.0', self.ep.client_stream_id, '0.0.0.0')
        self.ep.update_client_state(False)
        sock.sendto(packet.serialize(), (self.ep.get_neighbours_to_rp(), self.ep.port))
        self.master.destroy()  # Close the gui window

    def pause_movie(self):
        """Pause button handler."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        packet = Packet(PacketType.LEAVE, '0.0.0.0', self.ep.client_stream_id, '0.0.0.0')
        self.ep.update_client_state(False)
        sock.sendto(packet.serialize(), (self.ep.get_neighbours_to_rp(), self.ep.port))

    def play_movie(self):
        """Play button handler."""

        # Create a new thread to listen for RTP packets
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        packet = Packet(PacketType.JOIN, '0.0.0.0', self.ep.client_stream_id, '0.0.0.0').serialize()
        response = False
        address = (self.ep.get_neighbour_to_rp(), self.ep.port)
        while not response:
            sock.sendto(packet, address)
            try:
                resp, _ = sock.recvfrom(4096)
                packet = Packet.deserialize(resp)
                if packet.type == PacketType.ACK:
                    response = True
            except socket.timeout:
                pass

        print(f'Sending the JOIN {address}')
        self.ep.update_client_state(True)
        threading.Thread(target=self.listen_rtp).start()

    def listen_rtp(self):
        """Listen for RTP packets."""
        while True:
            try:
                data = self.ep.get_packet_from_buffer()
                if data:
                    rtp = RtpPacket()
                    rtp.decode(data)

                    curr_frame_nbr = rtp.seqNum()
                    print("Current Seq Num: " + str(curr_frame_nbr))

                    # if currFrameNbr > self.frameNbr:  # Discard the late packet
                    self.frameNbr = curr_frame_nbr
                    self.update_movie(rtp.getPayload())

            except Exception as exc:
                print(type(exc))
                print(exc.args)

    def update_movie(self, image_data):
        """Update the image file as video frame in the GUI."""
        image = Image.open(io.BytesIO(image_data))
        photo = ImageTk.PhotoImage(image)
        self.label.configure(image=photo, height=288)
        self.label.image = photo

    def handler(self):
        """Handler on explicitly closing the GUI window."""
        self.pause_movie()
        if messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.exit_client()
        else:  # When the user presses cancel, resume playing.
            self.play_movie()
