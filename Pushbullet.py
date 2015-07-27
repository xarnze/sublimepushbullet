import sublime, sublime_plugin
import urllib.request
import xml.etree.ElementTree as etree 
import base64
import threading
import json
import os
import webbrowser
import sublime_requests as requests

class PushbulletSendNoteCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		keyEntered = self.check_api_key(self.view.window())
		if keyEntered == 1:
			data = {
				"type" : 'note',
				"title" : self.view.name(),
				"body" : self.view.substr(sublime.Region(0, self.view.size()))
			}
			thread = ApiCall(data, 'https://api.pushbullet.com/v2/pushes');
			thread.sublime = self
			thread.start()
			self.handle_threads(edit, thread)
			pass

	def handle_threads(self, edit, thread, offset=0, i=0, dir=1):
		if thread.is_alive():
			# This animates a little activity indicator in the status area
			before = i % 8
			after = (7) - before
			if not after:
				dir = -1
			if not before:
				dir = 1
			i += dir
			self.view.set_status('pushbullet', 'Pushing [%s=%s]' % \
				(' ' * before, ' ' * after))

			sublime.set_timeout(lambda: self.handle_threads(edit, thread,
				offset, i, dir), 100)
			return
		else:
			self.view.erase_status('pushbullet')

	def check_api_key(self, window):
		settings = sublime.load_settings('Pushbullet.sublime-settings')
		if settings.get("token") == None:
			sublime.message_dialog("Please Enter your Pushbullet API key")
			webbrowser.open("https://www.pushbullet.com/#settings")
			window.show_input_panel("API Key:", "", self.on_Api_key_entered, None, None)
			return 0
			pass
		return 1

	def on_Api_key_entered(self, result):
		settings = sublime.load_settings('Pushbullet.sublime-settings')
		settings.set("token", result)
		sublime.save_settings('Pushbullet.sublime-settings')
		self.run(None)

class PushbulletSendNoteToDeviceCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		thread = ApiCall(None, 'https://api.pushbullet.com/v2/devices');
		thread.sublime = self
		thread.start()
		self.handle_threads(edit, thread)

	def handle_threads(self, edit, thread, offset=0, i=0, dir=1):
		if thread.is_alive():
			# This animates a little activity indicator in the status area
			before = i % 8
			after = (7) - before
			if not after:
				dir = -1
			if not before:
				dir = 1
			i += dir
			self.view.set_status('pushbullet', 'Pushing [%s=%s]' % \
				(' ' * before, ' ' * after))

			sublime.set_timeout(lambda: self.handle_threads(edit, thread,
				offset, i, dir), 100)
			return
		else:
			self.view.erase_status('pushbullet')
			print(json.dumps(thread.result["devices"]).encode("utf8"))

class ApiCall(threading.Thread):
	def __init__(self, data, url):
		threading.Thread.__init__(self)
		self.data = data
		self.url = url  

	def run(self):
		req = urllib.request.Request(self.url);
		settings = sublime.load_settings('Pushbullet.sublime-settings')
		authheader =  "Bearer " + settings.get("token")
		req.add_header("Authorization", authheader);
		if self.data != None:
			req.add_header('Content-Type', 'application/json')
			pass
		response = urllib.request.urlopen(req, json.dumps(self.data).encode("utf8"))
		encoding = response.headers.get_content_charset()
		data = json.loads(response.readall().decode(encoding))
		response.close()
		self.result = data
