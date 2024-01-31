#!/usr/bin/python3

# This is the same as mjpeg_server.py, but uses the h/w MJPEG encoder.

import io
import logging
import socketserver
from http import server
from threading import Condition

from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput


import time
from datetime import datetime
import subprocess

PAGE = """\
<html>
<style type = "text/css">

        body{font-family: Arial; margin:0px auto; background-color:powderblue;}
        
		img {
		float: down;
		margin: 20px;
		}
			
		.pics {
		clear: both;
		}
			
		/*rotate 180 degrees*/
		#rotate180 {
		/*General*/
		transform: rotate(180deg);
		/*Firefox*/
		-moz-transform: rotate(180deg);
		/*Microsoft Internet Explorer*/
		-ms-transform: rotate(180deg);
		/*Chrome, Safari*/
		-webkit-transform: rotate(180deg);
		/*Opera*/
		-o-transform: rotate(180deg);
		/*alter opacity*/
		//opacity:0.4;
		//filter:alpha(opacity = 40);
		}
			
		.infoContainer{
         background-color: powderblue;
         display: inline-block;
         text-align: center;
         margin-left: 10px;
         margin-top: 10px;
         border: 1px solid black;
         border-radius: 15px;
         float: left;
         width: auto;
         min-width:150px;
         min-height:320px;
         padding: 0 30px;
         box-sizing: border-box;
         box-shadow: 20px 20px 30px rgba(0,0,0,0.1);
         }        

         .innerInfo {
         background-color: #ffffff;
         display: inline-block;
         text-align: center;
         margin-left: 5px;
         margin-right: 5px;
         margin-top: 5px;
         margin-bottom: 15px;
         padding-bottom: 15px;
         border: 1px solid black;
         border-radius: 15px;
         width: auto;
         min-width: 50px;
         min-height:150px;
         padding: 5px;
         box-sizing: border-box;
         box-shadow: 20px 20px 30px rgba(0,0,0,0.1);
         }	
		</style>
<head>
<title>picamera2 MJPEG streaming demo</title>
</head>
<body oncopy="return false" oncut="return false" onpaste="return false">
<div class="Container">
             
<div class="infoContainer">
<h1>Pi Zero2w Cam/h1>
<div class="innerInfo">
<img src="stream.mjpg" width="640" height="480" id="rotate180">
</div>
</div>

<div class="infoContainer">
<h2>System Info</h2>
<span id="rntime" class="rnt"></span>
<br>
<iframe src="info.html"width="80%" height="120" style="border:1px solid black;"></iframe>
<br>
<button onclick=window.location.href='record.html';"">Record</button>
<br>
<button onclick=window.location.href='snap.html';"">Snap</button>
</div>

</div>

<script>
 window.onload = function timeNow() {
  var CurrentTime = new Date(),
    h = (CurrentTime.getHours()<10?'0':'') + CurrentTime.getHours();
    m = (CurrentTime.getMinutes()<10?'0':'') + CurrentTime.getMinutes();
    s = (CurrentTime.getSeconds()<10?'0':'') + CurrentTime.getSeconds();

var rntime = h + ":" + m +":" + s;

document.getElementById("rntime").innerHTML = rntime;

setTimeout(timeNow,1000);


 }
 
 
 
</script>

</body>
</html>
"""


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
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/record.html':
            getrecord = open("/home/zero2w/Servers/record.html", "r")
            getrcrd = (getrecord.read())
            getrecord.close()
            content = getrcrd.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
            print("recording")
            subprocess.Popen('arecord -D dmic_sv -d 30 -f S32_LE record_$(date "+%b-%d-%y-%I:%M:%S-%p").wav -c 2', shell=True)
        elif self.path == '/snap.html':
            getsnap = open("/home/zero2w/Servers/snap.html", "r")
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
            still_config = picam2.create_still_configuration()
            time.sleep(1)
            job = picam2.switch_mode_and_capture_file(still_config, "snap_%s.jpg" % timestamp, wait=False)
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
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
output = StreamingOutput()
picam2.start_recording(MJPEGEncoder(), FileOutput(output))



try:
    address = ('', 8000)
    server = StreamingServer(address, StreamingHandler)
    server.serve_forever()
finally:
    picam2.stop_recording()
