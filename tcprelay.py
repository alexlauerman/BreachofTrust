import asyncore
import signal
import socket

class RelayConnection(asyncore.dispatcher):
  prevdatalen = 0
  datalen = 0

  def __init__(self, client, address):
      asyncore.dispatcher.__init__(self)
      self.client = client
      self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
      print "connecting to %s..." % str(address)
      self.connect(address)

  def handle_connect(self):
      print "connected."
      # Allow reading once the connection
      # on the other side is open.
      self.client.is_readable = True

  def handle_read(self):

      #check if file is empty and if so reset to 0
      f = open('./responsesize', 'r') 
      
      obj = f.readline()
      print "obj:" + obj
      if obj == "-1":
        self.datalen = 0
      f.close()

      data = self.recv(128)
      self.datalen += len(data)
      if self.datalen == self.prevdatalen+128:
        self.prevdatalen = self.datalen
        print "--Server in progress--"
        print data
        print self.datalen
        print "--Server in progress--"
      else:
        print "------server last packet------"
        print data
        print self.datalen
        print "------server last packet------"

        f = open('./responsesize', 'w') 
        f.write(str(self.datalen))
        f.close()

      self.client.send(data)

class RelayClient(asyncore.dispatcher):
  prevdatalen = 0
  datalen = 0

  def __init__(self, server, client, address):
      asyncore.dispatcher.__init__(self, client)
      self.is_readable = False
      self.server = server
      self.relay = RelayConnection(self, address)

  def handle_read(self):
      data = self.recv(128)
      self.datalen += len(data)
      if self.datalen != self.prevdatalen:
        self.prevdatalen = self.datalen
        #print "C"
        #print self.datalen
      #else:
      #  print "------client------"
      #  print data
      #  print self.datalen
      #  print "------client------"
      
      self.relay.send(data)

  def handle_close(self):
      print "Closing relay..."
      # If the client disconnects, close the
      # relay connection as well.
      self.relay.close()
      self.close()

  def readable(self):
      return self.is_readable



class RelayServer(asyncore.dispatcher):
  def __init__(self, bind_address, dest_address):
      asyncore.dispatcher.__init__(self)

      self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
      self.bind(bind_address)
      self.dest_address = dest_address
      self.listen(10)

  def handle_accept(self):
      conn, addr = self.accept()
      RelayClient(self, conn, self.dest_address)



def handleSigTERM():
    RelayClient.close()
signal.signal(signal.SIGTERM, handleSigTERM)  

#RelayServer(("0.0.0.0", 8086), ("www.veracode.com", 80))
#RelayServer(("0.0.0.0", 8086), ("127.0.0.1", 8888))
RelayServer(("0.0.0.0", 443), ("31.13.76.49", 443)) #listen on first, forward to second facebook
asyncore.loop()

