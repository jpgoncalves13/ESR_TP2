import os
import socket
import threading
import time
import tkinter.messagebox as messagebox
from datetime import datetime
from tkinter import *

from PIL import Image, ImageTk, ImageFile

from RtpPacket import RtpPacket
from stream_packet import Packet, PacketType

ImageFile.LOAD_TRUNCATED_IMAGES = True

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"


class Client:
    INIT = 0
    READY = 1
    PLAYING = 2
    state = INIT

    SETUP = 0
    PLAY = 1
    PAUSE = 2
    TEARDOWN = 3

    # Initiation..
    def __init__(self, master, serveraddr, serverport, rtpport, stream_id):
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.createWidgets()
        self.serverAddr = serveraddr
        self.serverPort = int(serverport)
        self.rtpPort = int(rtpport)
        self.stream_id = stream_id
        self.rtspSeq = 0
        self.sessionId = 0
        self.requestSent = -1
        self.teardownAcked = 0
        self.connectToServer()
        self.frameNbr = 0
        self.openRtpPort()

    # self.listenRtp()

    def createWidgets(self):
        """Build GUI."""
        # Create Setup button
        self.setup = Button(self.master, width=20, padx=3, pady=3)
        self.setup["text"] = "Setup"
        self.setup["command"] = self.setupMovie
        self.setup.grid(row=1, column=0, padx=2, pady=2)

        # Create Play button
        self.start = Button(self.master, width=20, padx=3, pady=3)
        self.start["text"] = "Play"
        self.start["command"] = self.playMovie
        self.start.grid(row=1, column=1, padx=2, pady=2)

        # Create Pause button
        self.pause = Button(self.master, width=20, padx=3, pady=3)
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=1, column=2, padx=2, pady=2)

        # Create Teardown button
        self.teardown = Button(self.master, width=20, padx=3, pady=3)
        self.teardown["text"] = "Teardown"
        self.teardown["command"] = self.exitClient
        self.teardown.grid(row=1, column=3, padx=2, pady=2)

        # Create a label to display the movie
        self.label = Label(self.master, height=19)
        self.label.grid(row=0, column=0, columnspan=4, sticky=W + E + N + S, padx=5, pady=5)

    def setupMovie(self):
        """Setup button handler."""
        if self.state == self.INIT:
            self.sendRtspRequest(self.SETUP)

    def exitClient(self):
        """Teardown button handler."""
        self.sendRtspRequest(self.TEARDOWN)
        self.master.destroy()  # Close the gui window
        os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)  # Delete the cache image from video

    def pauseMovie(self):
        """Pause button handler."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        packet = Packet(PacketType.LEAVE,'0.0.0.0',0,'0.0.0.0')
        sock.sendto(packet.serialize(), (self.serverAddr, self.serverPort))

    def playMovie(self):
        """Play button handler."""
        # if self.state == self.READY:
        # Create a new thread to listen for RTP packets
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        packet = Packet(PacketType.STREAMREQ,'0.0.0.0',1,'0.0.0.0')
        sock.sendto(packet.serialize(), (self.serverAddr, self.serverPort))
        print('STREAM REQUEST enviado ao ' + str(self.serverAddr) + ':' + str(self.serverPort))
        threading.Thread(target=self.listenRtp).start()
        self.playEvent = threading.Event()
        self.playEvent.clear()
        #self.sendRtspRequest(self.PLAY)

    def listenRtp(self):
        """Listen for RTP packets."""
        while True:
            try:
                data = self.rtpSocket.recv(20480)
                if data:
                    rtp = RtpPacket()
                    rtp.decode(Packet.deserialize(data).payload)

                    currFrameNbr = rtp.seqNum()
                    print("Current Seq Num: " + str(currFrameNbr))

                    #if currFrameNbr > self.frameNbr:  # Discard the late packet
                    self.frameNbr = currFrameNbr
                    self.updateMovie(self.writeFrame(rtp.getPayload()))

            except Exception as exc:
                print(type(exc))
                print(exc.args)

    #				print(exc)
    # Stop listening upon requesting PAUSE or TEARDOWN
    # if self.playEvent.isSet():
    # break

    # Upon receiving ACK for TEARDOWN request,
    # close the RTP socket
    #				if self.teardownAcked == 1:
    #					self.rtpSocket.shutdown(socket.SHUT_RDWR)
    #					self.rtpSocket.close()
    #					break

    def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
        timestamp = int(time.time())
        cachename = f"{CACHE_FILE_NAME}{self.sessionId}_{timestamp}{CACHE_FILE_EXT}"
        file = open(cachename, "wb")
        file.write(data)
        file.close()

        return cachename

    def updateMovie(self, imageFile):
        """Update the image file as video frame in the GUI."""
        photo = ImageTk.PhotoImage(Image.open(imageFile))
        self.label.configure(image=photo, height=288)
        self.label.image = photo
        os.remove(imageFile)

    def connectToServer(self):
        """Connect to the Server. Start a new RTSP/TCP session."""
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.rtspSocket.connect((self.serverAddr, self.serverPort))
        except:
            messagebox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' % self.serverAddr)

    def sendRtspRequest(self, requestCode):
        """Send RTSP request to the server."""

        # Setup request
        if requestCode == self.SETUP and self.state == self.INIT:
            threading.Thread(target=self.recvRtspReply).start()
            # Update RTSP sequence number.
            self.rtspSeq = 1

            # Write the RTSP request to be sent.
            request = (
                f"SETUP {self.stream_id}\n"
                f"CSeq: {self.rtspSeq}\n"
                f"Port: {self.rtpPort}\n"
            )

            # Keep track of the sent request.
            self.requestSent = self.SETUP

        # Play request
        elif requestCode == self.PLAY and self.state == self.READY:

            # Update RTSP sequence number.
            self.rtspSeq = 2

            # Write the RTSP request to be sent.
            request = (
                f"PLAY {self.stream_id}\n"
                f"CSeq: {self.rtspSeq}\n"
                # f"Port: {self.rtpPort}\n"
            )

            # Keep track of the sent request.
            self.requestSent = self.PLAY

        # Pause request
        elif requestCode == self.PAUSE and self.state == self.PLAYING:
            # Update RTSP sequence number.
            self.rtspSeq = 3

            # Write the RTSP request to be sent.
            request = (
                f"PAUSE {self.stream_id}\n"
                f"CSeq: {self.rtspSeq}\n"
                f"Port: {self.rtpPort}\n"  # VER MELHOR
            )

            # Keep track of the sent request.
            self.requestSent = self.PAUSE

        # Teardown request
        elif requestCode == self.TEARDOWN and not self.state == self.INIT:
            # Update RTSP sequence number.
            self.rtspSeq = 4

            # Write the RTSP request to be sent.
            request = (
                f"TEARDOWN {self.stream_id}\n"
                f"CSeq: {self.rtspSeq}\n"
                f"Port: {self.rtpPort}\n"  # VER MELHOR
            )

            # Keep track of the sent request.
            self.requestSent = self.TEARDOWN
        else:
            return -1

        # Send the RTSP request using rtspSocket.
        self.rtspSocket.send(request.encode("utf-8"))

        print('\nData sent:\n' + request)

    def recvRtspReply(self):
        """Receive RTSP reply from the server."""
        while True:
            reply = self.rtspSocket.recv(1024)

            if reply:
                self.parseRtspReply(reply.decode("utf-8"))
                print("Received reply:\n" + reply.decode("utf-8"))

            # Close the RTSP socket upon requesting Teardown
            if self.requestSent == self.TEARDOWN:
                self.rtspSocket.shutdown(socket.SHUT_RDWR)
                self.rtspSocket.close()
                break

    def parseRtspReply(self, data):
        """Parse the RTSP reply from the server."""
        lines = data.split('\n')
        seqNum = int(lines[1].split(' ')[1])

        # Process only if the server reply's sequence number is the same as the request's
        if seqNum == self.rtspSeq:
            session = int(lines[2].split(' ')[1])
            # New RTSP session ID
            if self.sessionId == 0:
                self.sessionId = session

            # Process only if the session ID is the same
            if self.sessionId == session:
                if int(lines[0].split(' ')[1]) == 200:
                    if self.requestSent == self.SETUP:

                        print("Entrou aqui")

                        # Update RTSP state.
                        self.state = self.READY

                        # Open RTP port.
                        self.openRtpPort()

                    elif self.requestSent == self.PLAY:
                        self.state = self.PLAYING

                    elif self.requestSent == self.PAUSE:
                        self.state = self.READY

                        # The play thread exits. A new thread is created on resume.
                        self.playEvent.set()

                    elif self.requestSent == self.TEARDOWN:
                        self.state = self.INIT
                        self.teardownAcked = 1

    def openRtpPort(self):
        """Open RTP socket binded to a specified port."""
        # Create a new datagram socket to receive RTP packets from the server
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Set the timeout value of the socket to 0.5sec
        self.rtpSocket.settimeout(0.5)

        try:
            # Bind the socket to the address using the RTP port given by the client user
            self.rtpSocket.bind(('', self.rtpPort))
        except:
            messagebox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' % self.rtpPort)

    def handler(self):
        """Handler on explicitly closing the GUI window."""
        self.pauseMovie()
        if messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.exitClient()
        else:  # When the user presses cancel, resume playing.
            self.playMovie()
