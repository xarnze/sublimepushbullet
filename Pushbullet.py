import sublime, sublime_plugin
import urllib.request
import xml.etree.ElementTree as etree 
import base64
import threading
import json
import os

class PushbulletSendNoteCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		thread = ApiCall();
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

class ApiCall(threading.Thread):
	def run(self):
		data = {
			"type" : 'note',
			"title" : self.sublime.view.name(),
			"body" : self.sublime.view.substr(sublime.Region(0, self.sublime.view.size()))
		}
		req = urllib.request.Request('https://api.pushbullet.com/v2/pushes');
		settings = sublime.load_settings('Pushbullet.sublime-settings')
		authheader =  "Bearer " + settings.get("token")
		req.add_header("Authorization", authheader);
		req.add_header('Content-Type', 'application/json')
		file = urllib.request.urlopen(req, json.dumps(data).encode("utf8"))

		file.close()
		self.result = data
