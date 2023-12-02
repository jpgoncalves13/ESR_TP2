import sys, socket, time
from stream_packet import Packet, PacketType
from video_stream import VideoStream
from rtp_packet import RtpPacket
from metrics_thread import MetricsThread
import re


def main():
    
    if len(sys.argv) < 2:
        print("server: try 'server --help' for more information")
        return

    # --help option
    if len(sys.argv) == 2 and sys.argv[1] == '--help':
        info = "Usage: server <rendezvouz-ip> <video_file> <stream_id>"
        print(info)
        return

    MetricsThread(5000, 4096).start()

    # Preparar a stream
    stream = VideoStream(sys.argv[2])
    rp_ip = sys.argv[1].split(':')[0]
    stream_id = sys.argv[3]
    rp_port = 5000
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    i = 0
    while True:
        stream = VideoStream(sys.argv[2])
        data = stream.nextFrame()
        while data:
            frameNumber = stream.frameNbr()
            print(i)
            time.sleep(10)
            i += 1
            try:
                rtp_packet = makeRtp(data, frameNumber)
                sock.sendto(Packet(PacketType.STREAM, '0.0.0.0', int(stream_id), '0.0.0.0', rtp_packet).serialize(),
                                (rp_ip, rp_port))
            except Exception as e:
                print(e)
                break
            data = stream.nextFrame()


def makeRtp(payload, frameNbr):
    """RTP-packetize the video data."""
    version = 2
    padding = 0
    extension = 0
    cc = 0
    marker = 0
    pt = 26 # MJPEG
    seqnum = frameNbr
    ssrc = 0

    rtpPacket = RtpPacket()

    rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)

    return rtpPacket.getPacket()


if __name__ == "__main__":
    main()
