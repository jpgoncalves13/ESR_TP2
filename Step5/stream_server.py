import sys, socket
from server.server import Server
from server.stream_packet import Packet, PacketType
from video_stream import VideoStream
from rtp_packet import RtpPacket
import time

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
    rp_port = 5000
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    i=0
    while True:
        data = stream.nextFrame()
        
        if data:
            frameNumber = stream.frameNbr()
            print(i)
            time.sleep(0.01)
            i+=1
            try:
                rtp_packet = makeRtp(data, frameNumber)
                sock.sendto(Packet('Stream1',PacketType.STREAM,0,0,0,[],[],rtp_packet).serialize(), (rp_ip, rp_port))
            except Exception as e:
                print(e)
                break
        
    
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