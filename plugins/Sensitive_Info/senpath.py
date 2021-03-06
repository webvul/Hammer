#!/usr/bin/python2.7
#coding:utf-8
import re
import sys
import os
import urllib2
import socket
import threading
import futures
import requests

from urlparse import urlparse
from dummy import *

info = {
	'NAME':'Sensitive File/Directory Discover',
	'AUTHOR':'yangbh',
	'TIME':'20140716',
	'WEB':'',
	'DESCRIPTION':'Sensitive file or directory such as: /admin, /conf, /backup /db'
}

ret = ''
# ----------------------------------------------------------------------------------------------------
#
# ----------------------------------------------------------------------------------------------------
def getCrawlerPaths(url):
	''' '''
	try:
		cf = CrawlerFile(url=url)
		urls = cf.getSection('Paths')
		return urls
	except Exception,e:
		print 'Exception:\t',e
		return [url]

def getCrawlerFileExts(url):
	''' '''
	try:
		cf = CrawlerFile(url=url)
		exts = cf.getSection('FileExtensions')
		return exts
	except Exception,e:
		print 'Exception:\t',e
		return []

def getCommonPaths(filename):
	''' '''
	try:
		paths = []
		filename = BASEDIR  + '/lib/db/sensitivefiles/' + filename 
		fp = open(filename,'r')
		for eachline in fp:
			eachline = eachline.replace('\r','')
			eachline = eachline.replace('\n','')
			if eachline == '':
				continue
			paths.append(eachline)
		fp.close()
		return paths
	except Exception,e:
		print 'Exception:\t',e
		return []

def generateUrls(url):
	''' '''
	try:
		urls = []
		paths = []
		exts = getCrawlerFileExts(url)
		files = ['DIR.txt']
		
		if '.asp' in exts:
			files.append('ASP.txt')
			files.append('MDB.txt')
		if '.aspx' in exts:
			files.append('ASPX.txt')
		if '.php' in exts:
			files.append('PHP.txt')
		jspfileexts = ('.jsp','.jhtml','.action','.do')
		for eachext in jspfileexts:
			if eachext in exts:
				files.append('JSP.txt')
				break
		# files = list(set(files))
		pprint(files)
		for eachfile in files:
			paths += getCommonPaths(eachfile)
		print len(paths)

		# wether nessary covering each path
		toppaths = getCrawlerPaths(url)

		for eachpath in paths:
			eachurl = url + eachpath
			urls.append(eachurl)

		# rule file urls
		# rule file by kttzd
		rulefile = BASEDIR + '/lib/db/sensitive_file.rule'
		target_url=re.match(r'\w+:\/\/\w+\.(.*?)\.\w+',url).group(1)
		args = {'com':target_url}
		rf = RuleFile(rulefile,args)
		rf._getRules()
		# print rf.ret
		for i in rf.ret:
			urls.append(url + '/' +i)

		urls = list(set(urls))
		# pprint(urls)
		return urls

	except Exception,e:
		print 'Exception:\t',e
		return []

def httpcrack(url,lock):
	global ret
	printinfo = None
	flg = False

	for i in range(3):
		# 改用requests库
		try:
			rq = requests.get(url,allow_redirects=False)
			print url,rq.status_code
			if rq.status_code in [200,401,403]:
				printinfo = url + '\t code:' + str(rq.status_code) + os.linesep
				# print printinfo
				flg = True
			break
		# 一些并发导致的异常
		except Exception,e:
			print 'Exception',url
		# try:
		# 	 httpcode = urllib2.urlopen(url).getcode()
		# 	 if httpcode == 200:
		# 	 	printinfo = url + '\tcode:' + str(httpcode) + os.linesep
		# 	 	flg = True
		# 	 break
		# except socket.timeout,e:
		# 	continue
		# except Exception,e:
		# 	if type(e) == urllib2.HTTPError:
		# 		if e.getcode() in [401,403]:
		# 			flg = True
		# 		printinfo = url + '\tcode:' + str(e.getcode()) + os.linesep
		# 	else:
		# 		printinfo = url + '\tException' + str(e) + os.linesep
		# 	break

	lock.acquire()
	if printinfo:
		print printinfo,
		if flg:
			ret += printinfo
	lock.release()

	return(flg,printinfo)

def Audit(services):
	retinfo = {}
	output = ''
	if services.has_key('url') and not services.has_key('cms'):
		output += 'plugin run' + os.linesep
		urls = generateUrls(services['url'])
		pprint(urls)

		#  threads
		lock = threading.Lock()
		threads = []
		maxthreads = 20

		# for url in urls:
		# 	th = threading.Thread(target=httpcrack,args=(url,lock))
		# 	threads.append(th)
		# i = 0
		# while i<len(threads):
		# 	if i+maxthreads >len(threads):
		# 		numthreads = len(threads) - i
		# 	else:
		# 		numthreads = maxthreads
		# 	print 'threads:',i,' - ', i + numthreads

		# 	# start threads
		# 	for j in range(numthreads):
		# 		threads[i+j].start()

		# 	# wait for threads
		# 	for j in range(numthreads):
		# 		threads[i+j].join()

		# 	i += maxthreads
		# 改用futures模块
		with futures.ThreadPoolExecutor(max_workers=maxthreads) as executor:      #默认10线程
			future_to_url = dict((executor.submit(httpcrack, url, lock), url)
						 for url in urls)
	
	if ret != '':
		retinfo = {'level':'low','content':ret}
		security_warning(str(ret))
		
	return (retinfo,output)
# ----------------------------------------------------------------------------------------------------
#
# ----------------------------------------------------------------------------------------------------
if __name__=='__main__':
	url='http://www.eguan.cn'
	if len(sys.argv) ==  2:
		url = sys.argv[1]
	services = {'url':url}
	pprint(Audit(services))
	pprint(services)