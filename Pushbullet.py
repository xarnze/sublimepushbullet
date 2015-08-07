import sublime, sublime_plugin
import urllib.request
import xml.etree.ElementTree as etree 
import base64
import threading
import json
import os
import array
import webbrowser
import requests
# Disable HTTPS verification warnings.
from requests.packages import urllib3
urllib3.disable_warnings()

class PushbulletSendNoteCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		keyEntered = self.check_api_key(self.view.window())
		if keyEntered == 1:
			for item in Pushbullet().get_push_text(self.view):
				Pushbullet().send_note(None, "note", self.view.name(), item)
			pass

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
		PushbulletSendNoteCommand(self).check_api_key(self.view.window())
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
			self.view.set_status('pushbullet', 'Getting devices [%s=%s]' % \
				(' ' * before, ' ' * after))

			sublime.set_timeout(lambda: self.handle_threads(edit, thread,
				offset, i, dir), 100)
			return
		else:
			self.view.erase_status('pushbullet')
			device_list = []
			pushable_devices = []
			for device in thread.result["devices"]:
				if device["pushable"]:
					pushable_devices.append(device)
					device_list.append(device["nickname"])
					pass
				pass
			self.devices = pushable_devices
			self.view.window().show_quick_panel(device_list, self.on_device_selected)

	def on_device_selected(self, result):
		if result != -1:
			selected_device = self.devices[result]
			for item in Pushbullet().get_push_text(self.view):
				Pushbullet().send_note(selected_device["iden"], "note", self.view.name(), item, self.view)
			pass

class PushbulletSendNoteToContactCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		PushbulletSendNoteCommand(self).check_api_key(self.view.window())
		thread = ApiCall(None, 'https://api.pushbullet.com/v2/contacts');
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
			self.view.set_status('pushbullet', 'Getting contacts [%s=%s]' % \
				(' ' * before, ' ' * after))

			sublime.set_timeout(lambda: self.handle_threads(edit, thread,
				offset, i, dir), 100)
			return
		else:
			self.view.erase_status('pushbullet')
			device_list = []
			pushable_devices = []
			for device in thread.result["contacts"]:
				if device["active"]:
					pushable_devices.append(device)
					device_list.append(device["name"])
					pass
				pass
			self.devices = pushable_devices
			self.view.window().show_quick_panel(device_list, self.on_device_selected)

	def on_device_selected(self, result):
		if result != -1:
			selected_device = self.devices[result]
			for item in Pushbullet().get_push_text(self.view):
				Pushbullet().send_note(None, "note", self.view.name(), item, self.view, selected_device["email"])
			pass

class Pushbullet:
	def send_note(self, device, note_type, title, body, view, email=None):
		if device != None:
			data = {
				"device_iden": device,
				"type" : note_type,
				"title" : title,
				"body" : body
			}
			pass
		elif email != None:
			data = {
				"type" : note_type,
				"title" : title,
				"body" : body,
				"email" : email
			}
		else:
			data = {
				"type" : note_type,
				"title" : title,
				"body" : body
			}
		thread = ApiCall(data, 'https://api.pushbullet.com/v2/pushes');
		thread.start()
		self.handle_threads(view, "Pushing", None, None, thread)

	def handle_threads(self, view, waiting_message, callback, edit, thread, offset=0, i=0, dir=1):
		if thread.is_alive():
			# This animates a little activity indicator in the status area
			before = i % 8
			after = (7) - before
			if not after:
				dir = -1
			if not before:
				dir = 1
			i += dir
			view.set_status('pushbullet', waiting_message + ' [%s=%s]' % \
				(' ' * before, ' ' * after))

			sublime.set_timeout(lambda: self.handle_threads(view, waiting_message, callback, edit, thread,
				offset, i, dir), 100)
			return
		else:
			view.erase_status('pushbullet')
			if callback != None:
				callback()
				pass

	def get_push_text(self, view):
		selections = view.sel()
		selection_texts = []
		for selection in selections:
			text = view.substr(selection)
			if text:
				selection_texts.append(text)
				pass

		if not selection_texts:
			selection_texts.append(view.substr(sublime.Region(0, view.size())))
			pass
		return selection_texts

class ApiCall(threading.Thread):
	def __init__(self, data, url):
		threading.Thread.__init__(self)
		self.data = data
		self.url = url  

	def run(self):
		settings = sublime.load_settings('Pushbullet.sublime-settings')
		authheader =  "Bearer " + settings.get("token")
		headers = {"Authorization":authheader}
		session = requests.session()
		response = None
		if self.data != None:
			headers["Content-Type"] = 'application/json'
			response = session.post(self.url, data=json.dumps(self.data).encode("utf8"), headers=headers)
		else:
			response = session.get(self.url, headers=headers)

		data = response.json()
		response.close()
		self.result = data
