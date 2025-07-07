from socket import *
import socket
import threading
import time
import sys
import logging
from http import HttpServer

httpserver = HttpServer()

class ProcessTheClient(threading.Thread):
	def __init__(self, connection, address):
		self.connection = connection
		self.address = address
		threading.Thread.__init__(self)

	def run(self):
		rcv=""
		while True:
			try:
				data = self.connection.recv(1024)
				if data:

					#merubah input dari socket (berupa bytes) ke dalam string
					#agar bisa mendeteksi \r\n
					d = data.decode()
					rcv=rcv+d
					if '\r\n\r\n' in rcv:
						#end of command, proses string
						header_end = rcv.find('\r\n\r\n')
						headers = rcv[:header_end]
						body = rcv[header_end+4:].strip()
						logging.warning("Header dari client:\n{}".format(headers))
						logging.warning("Body dari client (command): {}".format(body))
						hasil = httpserver.proses(rcv)
						hasil = hasil + "\r\n\r\n".encode()
						logging.warning("balas ke client: {}".format(hasil))
						self.connection.sendall(hasil)
						rcv = ""
						self.connection.close()
				else:
					break
			except OSError as e:
				pass
		self.connection.close()

class Server(threading.Thread):
	def __init__(self):
		self.the_clients = []
		self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		threading.Thread.__init__(self)

	def run(self):
		self.my_socket.bind(('0.0.0.0', 8889))
		self.my_socket.listen(10)
		while True:
			self.connection, self.client_address = self.my_socket.accept()
			logging.warning("connection from {}".format(self.client_address))

			clt = ProcessTheClient(self.connection, self.client_address)
			clt.start()
			self.the_clients.append(clt)

def main():
	svr = Server()
	svr.start()

if __name__=="__main__":
	main()
