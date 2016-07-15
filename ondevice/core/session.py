from ondevice.core import config, sock, service
from ondevice import modules

import json
import logging
import threading
import traceback
import sys

class Session(sock.Socket):
	""" Connects to the ondevice service """
	def __init__(self):
		devId = config.getDeviceId()
		kwargs = {}
		if devId != None:
			kwargs['id'] = devId

		auth = (config.getDeviceUser(), config.getDeviceAuth())
		sock.Socket.__init__(self, '/serve', auth=auth, **kwargs)

	def onMessage(self, msg):
		try:
			if not '_type' in msg:
				raise Exception("Missing message type: {0}".format(msg))
			elif msg._type == 'hello':
				assert not self._connectionSucceeded
				logging.info("Connection established, online as '%s'", msg.name)
				config.setDeviceName(msg.name)
				self._devId = msg.devId
				self._sid = msg.sid
				config.setDeviceId(msg.devId)

				for name, svc in service.listServices().items():
					self.send({'_type': 'announce', 'name': name, 'protocol': svc['protocol']})

				self._connectionSucceeded = True
			elif msg._type == 'ping':
				# send back a 'pong' message
				logging.debug("Got ping: %s", repr(msg))
				response = {'_type': 'pong', 'ts': msg.ts}
				self.send(response)
			elif msg._type == 'connect':
				logging.info("Got '%s' request by user %s (ip: %s)", msg.service, msg.clientUser, msg.clientIp)
				try:
					svc = modules.getService(msg, self._devId)

					svc.startRemote()
					svc.startLocal()
				except Exception as e:
					# got error -> notify the server
					self.send({'_type': 'connectError', 'tunnelId': msg.tunnelId, 'code': 502, 'msg': repr(e)})
					raise e

			elif msg._type == 'error':
				errType = 'Error'
				if msg.code == 400: errType = 'Bad Request'
				elif msg.code == 403: errType = 'Forbidden'
				elif msg.code == 404: errType = 'Not Found'

				logging.error("%s: %s", errType, msg.msg)
			else:
				logging.error("onMessage: unsupported type")
				logging.error("  msg=%s", msg)
		except Exception as e:
			# the websocket-client lib swallows the stack traces of exceptions
			print("Msg: '{0}'".format(msg))
			traceback.print_exc()
			raise e

	def run(self):
		self._connectionSucceeded = False
		sock.Socket.run(self)
		return self._connectionSucceeded

	def send(self, msg):
		data = json.dumps(msg)
		logging.debug('>> %s', data)
		self._ws.send(data)
