#!/usr/bin/python3

# Mostly copied from https://picamera.readthedocs.io/en/release-1.13/recipes2.html
# Run this script, then point a web browser at http:<this-ip-address>:8000
# Note: needs simplejpeg to be installed (pip3 install simplejpeg).

import io
import logging
import socketserver
from http import server
from threading import Condition

from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput

from libcamera import Transform

import time
from datetime import datetime
import subprocess

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(16,GPIO.OUT)
GPIO.setup(16,GPIO.LOW)

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
            
        elif self.path == '/index.html':
            getinfo = open("/home/allzero21/Webserver/birdcam/public/index.html", "r")
            getinf = (getinfo.read())
            getinfo.close()
            content = getinf.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content) 
            
        elif self.path == '/mystyles.css':
            getinfo = open("/home/allzero21/Webserver/birdcam/public/css/mystyles.css", "r")
            getinf = (getinfo.read())
            getinfo.close()
            content = getinf.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/css')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        
        elif self.path == '/favicon.ico':
            getinfo = open("/home/allzero21/Webserver/birdcam/public/favicon.ico", "r")
            getinf = (getinfo.read())
            getinfo.close()
            content = getinf.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'image/x-icon')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
                      
        elif self.path == '/snap.html':
            getsnap = open("/home/allzero21/Webserver/birdcam/public/snap.html", "r")
            getsnp = (getsnap.read())
            getsnap.close()
            content = getsnp.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
            print("snap")
            timestamp = datetime.now().isoformat("_","seconds")
            still_config = picam2.create_still_configuration(transform=Transform(hflip=1, vflip=1))
            time.sleep(1)
            job = picam2.switch_mode_and_capture_file(still_config, "/home/allzero21/Webserver/birdcam/public/photo/snap_%s.jpg" % timestamp, wait=False)
            print(timestamp)
            time.sleep(1)
        
        elif self.path == '/record.html':
            getrecord = open("/home/allzero21/Webserver/birdcam/public/record.html", "r")
            getrcrd = (getrecord.read())
            getrecord.close()
            content = getrcrd.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
            print("recording")
            subprocess.Popen('arecord -D dmic_sv -d 30 -f S32_LE /home/allzero21/Webserver/birdcam/public/record/birdcam_$(date "+%b-%d-%y-%I:%M:%S-%p").wav -c 2', shell=True)
        
        elif self.path == '/info.html':
            getinfo = open("/home/allzero21/Webserver/birdcam/public/info.html", "r")
            getinf = (getinfo.read())
            getinfo.close()
            content = getinf.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        
        elif self.path == '/led_on':
            getinfo = open("/home/allzero21/Webserver/birdcam/public/led_on.html", "r")
            getinf = (getinfo.read())
            getinfo.close()
            content = getinf.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
            print("led on")
            GPIO.output(16,GPIO.HIGH)
        
        elif self.path == '/led_off':
            getinfo = open("/home/allzero21/Webserver/birdcam/public/led_off.html", "r")
            getinf = (getinfo.read())
            getinfo.close()
            content = getinf.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
            print("led off")
            GPIO.output(16,GPIO.LOW)
        
        elif self.path == '/watch.html':
            getinfo = open("/home/allzero21/Webserver/birdcam/public/watch.html", "r")
            getinf = (getinfo.read())
            getinfo.close()
            content = getinf.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}, transform=Transform(hflip=1, vflip=1)))
output = StreamingOutput()
picam2.start_recording(MJPEGEncoder(), FileOutput(output))

try:
    address = ('', 8000)
    server = StreamingServer(address, StreamingHandler)
    server.serve_forever()
finally:
    picam2.stop_recording()
    GPIO.output(16,GPIO.LOW)