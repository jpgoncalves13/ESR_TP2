import sys, socket
from video_stream import VideoStream
from rtp_packet import RtpPacket
from server.stream_packet import Packet, PacketType

def main():
    if len(sys.argv) < 2:
        print("server: try 'server --help' for more information")
        return

    # --help option
    if len(sys.argv) == 2 and sys.argv[1] == '--help':
        info = "Usage: server <rendezvouz-ip(:bootstrapper-port)?> <video_file>"
        print(info)
        return

    # Preparar a stream
    stream = VideoStream(sys.argv[2])
    rp_ip = sys.argv[1].split(':')[0]
    rp_port = int(sys.argv[1].split(':')[1])
    socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        data = stream.nextFrame()
        if data:
            frameNumber = stream.frameNbr()
            try:
                rtp_packet = makeRtp(data, frameNumber)
                socket.sendto(Packet(0,PacketType.STREAM,0,0,0,0,0,rtp_packet).serialize(), (rp_ip, rp_port))
            except:
                print("Connection Error")
    
def makeRtp(payload, frameNbr):
	"""RTP-packetize the video data."""
	version = 2
	padding = 0
	extension = 0
	cc = 0
	marker = 0
	pt = 26 # MJPEG type
	seqnum = frameNbr
	ssrc = 0 
	
	rtpPacket = RtpPacket()
	
	rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)
	
	return rtpPacket.getPacket()
    

if __name__ == "__main__":
	main()