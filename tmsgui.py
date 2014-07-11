#tmsgui.py

import wx
from wx.lib import intctrl
#import os
#import signal
import subprocess

import web
import Magstim.Rapid2Constants
from Magstim.MagstimInterface import Rapid2
import sys
import argparse
import time
import requests
from threading import Lock, Thread, Event

"""
Where the TMS machine is connected to this computer
"""
SERIAL_PORT = 'COM1'

"""
"""
POWER_THRESHOLD = 80;

"""
"""
PERCENT_THRESHOLD = 100;

from mock import patch, MagicMock
import server

urls = (
    '/', 'index',
    '/TMS/arm', 'tms_arm',
    '/TMS/disarm', 'tms_disarm',
    '/TMS/fire', 'tms_fire',
    '/TMS/power/(\d*)', 'tms_intensity'
)

DEFAULT_PORT = 25000

class MainWindow(wx.Frame):
	
	def __init__(self, parent, title):
		
		"""
		set default values
		"""
		self.port = DEFAULT_PORT
		self.intensity = POWER_THRESHOLD
		
		wx.Frame.__init__(self, parent, title = title, size = (500, 500))
		self.CreateStatusBar()
		
		"""
		Create higher-level layout structure
		"""
		self.panel = wx.Panel(self)
		self.controlLevelSizer = wx.BoxSizer(wx.VERTICAL)
				
		"""
		Create port connection widgets
		"""
		self.portSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.connectText = wx.StaticText(self.panel, label = 'Connect to Port:                      ')
		self.portSizer.Add(self.connectText, flag = wx.RIGHT | wx.TOP | wx.LEFT, border = 15)
		
		self.portCtrl = intctrl.IntCtrl(self.panel, value = self.port)
		self.portSizer.Add(self.portCtrl, flag = wx.RIGHT | wx.TOP, border = 10)
		
		self.connectButton = wx.Button(self.panel, -1, 'Connect')
		self.portSizer.Add(self.connectButton, flag = wx.TOP, border = 8)
		self.Bind(wx.EVT_BUTTON, self.ConnectToPort, self.connectButton)
		
		"""
		Create port disconnection widgets
		"""
		self.disconnectText = wx.StaticText(self.panel, label = 'Currently Connected to Port:')
		self.disconnectText.Hide()
		
		self.disconnectButton = wx.Button(self.panel, -1, 'Disconnect')
		self.disconnectButton.Hide()
		self.Bind(wx.EVT_BUTTON, self.DisconnectFromPort, self.disconnectButton)
		
		self.portSizer.Layout()
		
		"""
		Add port connection/disconnection box sizer and separating line
		to larger vertical sizer
		"""
		self.controlLevelSizer.Add(self.portSizer, flag = wx.EXPAND|wx.BOTTOM, border = 10)
		self.line1 = wx.StaticLine(self.panel)
		self.controlLevelSizer.Add(self.line1, flag = wx.EXPAND|wx.BOTTOM, border = 10)
		
		"""
		Create intensity and arm/disarm controls
		"""
		self.controlSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.intensityText = wx.StaticText(self.panel, label = 'Intensity Level:')
		self.intensityCtrl = intctrl.IntCtrl(self.panel, value = self.intensity)
		self.armButton = wx.Button(self.panel, -1, 'Arm TMS')
		self.Bind(wx.EVT_BUTTON, self.Arm, self.armButton)
		self.disarmButton = wx.Button(self.panel, -1, 'Disarm TMS')
		self.Bind(wx.EVT_BUTTON, self.Disarm, self.disarmButton)
		self.controlSizer.Add(self.intensityText, flag = wx.RIGHT | wx.TOP | wx.LEFT, border = 15)
		self.controlSizer.Add(self.intensityCtrl, flag = wx.RIGHT | wx.TOP, border = 10)
		self.controlSizer.Add(self.armButton, flag = wx.TOP, border = 8)
		self.controlSizer.Add(self.disarmButton, flag = wx.TOP, border = 8)
		
		self.controlLevelSizer.Add(self.controlSizer, flag = wx.EXPAND|wx.BOTTOM, border = 10)
		self.intensityText.Hide()
		self.intensityCtrl.Hide()
		self.armButton.Hide()
		self.disarmButton.Hide()
		
		self.line2 = wx.StaticLine(self.panel)
		self.controlLevelSizer.Add(self.line2, flag = wx.EXPAND|wx.BOTTOM, border = 10)
		self.controlLevelSizer.Show(self.line2, False)
		
		"""
		Wrap up layout instructions
		"""
		self.controlLevelSizer.Layout()
		self.panel.SetSizer(self.controlLevelSizer)
		self.Layout()
		self.Show()
		
		#self.serverProcess = None
		self.serverThread = None
	
	"""
	Remove connection widgets
	Replace with disconnection widgets.
	Start a new thread to run the server
	"""
	def ConnectToPort(self, e):
		self.port = self.portCtrl.GetValue()
		self.portSizer.Detach(self.connectText)
		self.connectText.Hide()
		self.portSizer.Detach(self.portCtrl)
		self.portCtrl.Hide()
		self.portSizer.Detach(self.connectButton)
		self.connectButton.Hide()
		
		self.portSizer.Add(self.disconnectText, flag = wx.RIGHT | wx.TOP | wx.LEFT, border = 15)
		self.portSizer.Show(self.disconnectText, True)
		self.portSizer.Add(self.portCtrl, flag = wx.RIGHT | wx.TOP, border = 10)
		self.portCtrl.SetEditable(False)
		self.portCtrl.SetBackgroundColour('LIGHT GREY')
		self.portSizer.Show(self.portCtrl, True)
		self.portSizer.Add(self.disconnectButton, flag = wx.TOP, border = 8)
		self.portSizer.Show(self.disconnectButton, True)
		self.portSizer.Layout()
		
		self.controlLevelSizer.Show(self.controlSizer, True)
		self.intensityText.Show()
		self.intensityCtrl.Show()
		self.armButton.Show()
		self.disarmButton.Hide()
		self.controlLevelSizer.Show(self.line2, True)
		self.controlSizer.Layout()
		self.controlLevelSizer.Layout()
		
		#self.serverProcess = subprocess.Popen(["serverRun(self.port)"], shell = False)
		print 'Connecting to port ' + str(self.port)
		self.serverThread = ServerThread(port = self.port)
		#self.serverThreadID = self.serverThread.getpid()
				
	def DisconnectFromPort(self, e):
		print 'Disconnecting from port ' + str(self.port)
		#os.kill(self.serverThreadID, signal.CTRL_C_EVENT)
		#self.serverThread._abort()
		sys.exit()
		
		"""
		self.port = None
		self.portSizer.Detach(self.disconnectText)
		self.disconnectText.Hide()
		self.portSizer.Detach(self.portCtrl)
		self.portCtrl.Hide()
		self.portSizer.Detach(self.disconnectButton)
		self.disconnectButton.Hide()
		
		self.portSizer.Add(self.connectText, flag = wx.RIGHT | wx.TOP | wx.LEFT, border = 15)
		self.portSizer.Show(self.connectText, True)
		self.portSizer.Add(self.portCtrl, flag = wx.RIGHT | wx.TOP, border = 10)
		self.portCtrl.SetEditable(True)
		self.portCtrl.SetBackgroundColour(wx.NullColour)
		self.portSizer.Show(self.portCtrl, True)
		self.portSizer.Add(self.connectButton, flag = wx.TOP, border = 8)
		self.portSizer.Show(self.connectButton, True)
		self.portSizer.Layout()
		"""
		#self.serverProcess.terminate()
	"""
	Arm the TMS, lock the intensity, allow option to fire
	"""
	def Arm(self, e):
		self.intensity = self.intensityCtrl.GetValue()
		self.intensityCtrl.SetEditable(False)
		self.intensityCtrl.SetBackgroundColour('LIGHT GREY')
		
		self.armButton.Hide()
		self.disarmButton.Show()
		self.controlSizer.Layout()
		
		#setPower = subprocess.Popen(['setPower.py', str(self.port), str(self.intensity)])
		
		res = requests.post('http://localhost:%d/TMS/power/%d' % (self.port, self.intensity))
		print res.status_code, res.text
		res.close()
		
		res = requests.post('http://localhost:%d/TMS/arm' % self.port)
		print res.status_code, res.text
		res.close()
	
	"""
	Disarm the TMS, taking away the Fire option and allowing to change intensity
	"""
	def Disarm(self, e):
		self.intensityCtrl.SetEditable(True)
		self.intensityCtrl.SetBackgroundColour(wx.NullColour)
		
		self.disarmButton.Hide()
		self.armButton.Show()
		self.controlSizer.Layout()
		
		res = requests.post('http://localhost:%d/TMS/disarm' % self.port)
		print res.status_code, res.text
		res.close()
	
"""		
def isInt(s):
	try:
		int(s)
		return True
	except ValueError:
		return False
"""	

"""
A class that keeps the server running in its own thread,
which can be stopped by disconnecting from the port that
the server is on
"""
class ServerThread(Thread):
	
	def __init__(self, port):
		Thread.__init__(self)
		self.port = port
		#self.abort = Event()
		#self.abort = False
		self.setDaemon(True)
		#self.serverProcess = None
		self.start()
	
	"""
	def _abort(self):
		self.serverProcess.terminate()
		#self.abort = True
		#print 'Server Thread Aborting at port ' + str(self.port)
		#self.abort.set()
		#sys.exit()
	"""
	
	"""
	def getpid(self):
		return os.getpid()
	"""
	
	def run(self):
		#self.serverProcess = subprocess.Popen(serverRun(self.port), shell = True)
		"""
		Toggle this portion with comments for real/mock server
		"""
		with patch('serial.Serial') as mockedSerialPort:
			serialObj = MagicMock()
			mockedSerialPort.side_effect = lambda: serialObj
	
			# Print out whatever is being written to the serial port
			def show_me(data):
				print data
			serialObj.write.side_effect = show_me
			
			do_main(self.port)
			
		"""		
		do_main(self.port)
		"""
		
		"""
		while True:
			#print 'Server Thread Running at port ' + str(self.port)
			time.sleep(0.5)
			print abort
			if self.abort: #.isSet():
				print 'Server Thread Aborting at port ' + str(self.port)
				return
		"""
"""		
def serverRun(port):
	serverThread = ServerThread(port = port)
"""
	
class index:
    """
    Returns a readme with how to use this API
    """

    def GET(self):
        with open('README.md', 'r') as f:
            return f.read()

class tms_arm:
    """
    Arms the TMS device
    """

    def POST(self):
        web.STIMULATOR_LOCK.acquire()
        web.STIMULATOR.armed = True

        # Wait a bit
        waitTime = (Magstim.Rapid2Constants.output_intesity[web.STIMULATOR.intensity] - 1050) / 1050.0
        waitTime = max(0.5, waitTime)
        time.sleep(waitTime)
        
        # Just in case
        web.STIMULATOR.disable_safety()
        web.STIMULATOR_LOCK.release()
        
        # Return nothing
        web.ctx.status = '204 No Content'

class tms_disarm:
    """
    Disarms the TMS device
    """

    def POST(self):
        web.STIMULATOR_LOCK.acquire()
        web.STIMULATOR.armed = False
        web.STIMULATOR_LOCK.release()
        
        # Return nothing
        web.ctx.status = '204 No Content'

class tms_fire:
    """
    Triggers a TMS pulse
    """

    def POST(self):
        # Joseph this is the first log entry
        log_event("[TMS] Fire command received")
        web.STIMULATOR_LOCK.acquire()
        web.STIMULATOR.trigger()
        web.STIMULATOR_LOCK.release()
        
        # And this is the last 
        log_event("[TMS] Pulse fired")
        
        # Return nothing
        web.ctx.status = '204 No Content'
        
        # Allow Cross-Origin Resource Sharing (CORS)
        # This lets a web browser call this method with no problems
        web.header('Access-Control-Allow-Origin', web.ctx.env.get('HTTP_ORIGIN'))

class tms_intensity:
    """
    Sets the intensity level of the TMS
    """
    
    def POST(self, powerLevel):
        web.STIMULATOR_LOCK.acquire()
        web.STIMULATOR.intensity = int(powerLevel)
        web.STIMULATOR_LOCK.release()
        
        # Return nothing
        web.ctx.status = '204 No Content'


class maintain_communication(Thread):
    def run(self):
        while True:
            web.STIMULATOR_LOCK.acquire()
            web.STIMULATOR.remocon = True
            web.STIMULATOR_LOCK.release()

            time.sleep(0.5)

# Report all errors to the client
web.internalerror = web.debugerror		
		
def do_main(port):
    """
	# Take only a port as an argument
    parser = argparse.ArgumentParser(
            description='Opens a server to control the TMS machine on the given port')
    parser.add_argument('port', type=int)
    args = parser.parse_args()
	"""

    # Make sure that the server only listens to localhost
    # This is because we cannot allow outside computer to access the TMS
    sys.argv.append('127.0.0.1:%d' % port)

    # Initialize the shared state between web threads
    web.STIMULATOR = Rapid2(port=SERIAL_PORT)
    web.STIMULATOR_LOCK = Lock()
    web.STIMULATOR.remocon = True
    # Start the thread to keep the TMS awake
    poller = maintain_communication()
    poller.daemon = True
    poller.start()

    # Set the power level
    powerLevel = int(POWER_THRESHOLD * PERCENT_THRESHOLD / 100);
    if powerLevel > 100:
        powerLevel = 100
    elif powerLevel < 0:
        powerLevel = 0
    web.STIMULATOR.intensity = powerLevel
    web.STIMULATOR.disable_safety()

    # Start the server
    app = web.application(urls, globals())
    app.run()
	
app = wx.App(False)
frame = MainWindow(None, title = "TMS GUI")
app.MainLoop()