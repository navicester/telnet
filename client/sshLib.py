
#TestMgrLte

import time
import re
import socket
#import ioUtils
import logging
import traceback
import sys
import paramiko

class SSH_common:	
	def is_SSH_valid(self):
		# for debug
		#print "SSH Handle:  "+str(self.m_sshHandle)
		#print "SSH Channel:  "+str(self.m_sshChannel)
		return (self.m_sshHandle != None and self.m_sshChannel != None)
		
	def set_current_buffer(self):
		if not self.is_SSH_valid():
			raise socket.error, "SSH handle not valid anymore"
		
		bConnOK = True
		# lets test if the send is ready: if not, means the connection is deactivated: for instance a reboot of board
		try:
			bConnOK = self.m_sshHandle.get_transport().is_active()
		except KeyboardInterrupt as kb_e:
			raise kb_e
		except:
			print("Exception is_active")
			traceback.print_tb(sys.exc_info()[2])
			print(sys.exc_info())
			bConnOK = False
		if not bConnOK:
			print("Connection SSH not alive anymore. Closing ssh objects")
			self.close()
			raise socket.error("SSH channel not alive: channel and handle have been closed")

		try:
			self.m_sshChannel.setblocking(True)
			self.m_sshChannel.settimeout(0.5)
		except socket.error:
			print("Error on socket")
		try:
			while self.m_sshChannel.recv_ready():
				try:
					data = self.m_sshChannel.recv(1024)
					#self.m_tempBuffer+=data
					self.m_currentBuffer+=data
					self.m_sshChannel.settimeout(0.1)
				except socket.timeout:
					# la connection est tombee ou pas?... comment se fait il qu'on soit dans cet etat la?
					# est ce qu on essaie de la retablir?
					print("socket.timeout")
					traceback.print_tb(sys.exc_info()[2])
					print(sys.exc_info())
					break
				except socket.error:
					print("socket.error on self.m_sshChannel.recv or self.m_sshChannel.settimeout(0.1)")
					traceback.print_tb(sys.exc_info()[2])
					print(sys.exc_info())
					raise
		except socket.timeout:
			# la connection est tombee ou pas?... comment se fait il qu'on soit dans cet etat la?
			# est ce qu on essaie de la retablir?
			print("socket.timeout on self.m_sshChannel.recv_ready")
			traceback.print_tb(sys.exc_info()[2])
			print(sys.exc_info())
		except socket.error:
			print("socket.error on self.m_sshChannel.recv_ready if no previous exception on self.m_sshChannel.recv")
			traceback.print_tb(sys.exc_info()[2])
			print(sys.exc_info())
			raise
		
	# checks if node buffer is empty or not: if empty 2 times, send a Enter
	# the problem is that we should be able to discard the corresponding log, otherwise, it pollutes the server
	def check_is_alive(self):
		if len(self.m_currentBuffer) > 0:
			self.m_counterEmptyBuffer = 0
		else:
			self.m_counterEmptyBuffer += 1
			if self.m_counterEmptyBuffer > 1: #was 3 before but looks like it is not efficient enough
				self.m_counterEmptyBuffer = 0
				try:
					self.write("\n")
				except KeyboardInterrupt as kb_e:
					raise kb_e
				except Exception:
					print("No buffer received during 10 seconds: a write on SSH channel raises an exception. SSH connection may not be alive anymore. Closing ssh objects")
					self.close()
			
	def basic_check_is_alive(self):
		if not self.m_sshHandle.get_transport().is_active():
			self.close()
			raise socket.error("SSH handle transport is_active is false")
		try:
			self.write("\n")
		except KeyboardInterrupt as kb_e:
			raise kb_e
		except Exception:
			print("a write on SSH channel raises an exception. SSH connection may not be alive anymore. Closing ssh objects")
			self.close()
			
	def close(self):
		print("Closing SSH connection")
		try:
			self.m_sshChannel.close()
		except KeyboardInterrupt as kb_e:
			raise kb_e
		except Exception, e:
			print("Exception when trying to close SSH channel")
			print(e)
		self.m_sshChannel = None
		try:
			self.m_sshHandle.close()
		except KeyboardInterrupt as kb_e:
			raise kb_e
		except Exception, e:
			print("Exception when trying to close SSH handle")
			print(e)
		self.m_sshHandle = None
	
	def write(self, mystr):
		bitWritten = 0
		if self.m_sshChannel.send_ready():
			#time.sleep(2)
			#if ioUtils.inSimuMode() > 0:
			#	print("Channel ready: sending string ---" + mystr + "---")
			bitWritten = self.m_sshChannel.send(mystr+"\n")
		else:
			print("Channel not ready. Not sending " + mystr)
		return bitWritten
	
	def expect(self, lExpectedStrs, timeout):
		# il faut manager le timeout
		startTime = time.time()
		# il faut garder en stock la taille max des chaines a chercher: probleme pour expression regulare
		lCompiledStrs = lExpectedStrs[:]
		indices = range(len(lCompiledStrs))
		for i in indices:
			lCompiledStrs[i] = re.compile(lExpectedStrs[i], re.DOTALL)
		while (time.time() - startTime) < timeout:
			self.set_current_buffer()
			for i in indices:
				m = lCompiledStrs[i].search(self.m_currentBuffer)
				if m:
					e = m.end()
					text = self.m_currentBuffer[:e]
					self.m_currentBuffer = self.m_currentBuffer[e:]
					return (i, m, text)
		###############################
		# MAY BRING ERRORS @@@@@@@@
		###############################
		self.basic_check_is_alive()
		return (-1, None, self.m_currentBuffer)
		
	def read_very_lazy(self):
		self.set_current_buffer()
		returnBuffer = self.m_currentBuffer
		self.m_currentBuffer = ""
		return returnBuffer
		
	def read_very_eager(self):
		#time.sleep(2)
		self.set_current_buffer()
		returnBuffer = self.m_currentBuffer
		if returnBuffer.strip() != "":
			print(returnBuffer)
		self.m_currentBuffer = ""
		return returnBuffer
	
# reprendre tout pareil que TelnetLib: pas possible en fait car password doit etre integrer dans le connect
# ==> keyword SSH_Connect IP_address port login password timeout
# sshlib.SSH
class SSH(SSH_common):
	def __init__(self, IP_address, port, login, passwd, timeout):
		self.m_isConnected = False
		self.m_sshIP = IP_address
		self.m_sshPort = port
		self.m_sshLogin = login
		self.m_sshPass = passwd
		self.m_connTimeout = timeout
		self.eof = False
		
		self.m_sshHandle = None
		self.m_sshChannel = None
		
		# reset to zero when set_current_buffer is called
		self.m_tempBuffer = ""
		# only reset manually
		self.m_currentBuffer = ""
		
		self.m_counterEmptyBuffer = 0
		# deactivates INFO logging in your appli from paramiko
		logging.getLogger("paramiko").setLevel(logging.WARNING)
		
		self.connect()
		
	def connect(self):
		if self.m_sshHandle != None:
			self.close()
		time_begin = time.time()
		while time.time() - time_begin < self.m_connTimeout and not self.m_isConnected:
			try:
				self.m_sshHandle = paramiko.SSHClient()
			except KeyboardInterrupt as kb_e:
				raise kb_e
			except Exception, e:
				print("could not paramiko.SSHClient(), retrying")
				print(e)
				self.m_sshHandle = None
			else:
				try:
					self.m_sshHandle.set_missing_host_key_policy(paramiko.AutoAddPolicy())
				except KeyboardInterrupt as kb_e:
					raise kb_e
				except Exception, e:
					time.sleep(1)
					self.m_sshHandle = None
					print("could not set missing host key policy ssh, retrying")
					print(e)
				else:
					try:
						self.m_sshHandle.connect(self.m_sshIP, username=self.m_sshLogin, password=self.m_sshPass, timeout=20)
					except KeyboardInterrupt as kb_e:
						raise kb_e
					except Exception, e:
						self.m_sshHandle = None
						time.sleep(1)
						print("could not connect by ssh, retrying")
						print(e)
					else:
						self.m_isConnected = True
		if not self.m_isConnected:
			print("Impossible to connect SSH on address " + self.m_sshIP + " with login " + self.m_sshLogin + " and password " + self.m_sshPass)
		else:
			try:
				self.m_sshChannel = self.m_sshHandle.invoke_shell(term='dumb', width=80, height=24)
				print("SSH Connection successful")
			except paramiko.ChannelException, e:
				print("ChannelException")
				print(e)
			except KeyboardInterrupt as kb_e:
				raise kb_e
			except Exception, e:
				print("Unable to establish SSH channel")
				print(e)
				self.m_sshChannel = None
				self.m_sshHandle.close()
				self.m_sshHandle = None
				self.m_isConnected = False


class SSHKEY(SSH_common):
	def __init__(self, IP_address, port, login, private_key, pass_phrase, timeout):
		self.m_private_key_file=private_key
		self.m_key_passphrase=pass_phrase
		self.m_isConnected = False
		self.m_sshIP = IP_address
		self.m_sshPort = port
		self.m_sshLogin = login
		self.m_connTimeout = timeout
		self.eof = False
		
		self.m_sshHandle = None
		
		# reset to zero when set_current_buffer is called
		self.m_tempBuffer = ""
		# only reset manually
		self.m_currentBuffer = ""
		
		self.m_counterEmptyBuffer = 0
		# deactivates INFO logging in your application from paramiko
		logging.getLogger("paramiko").setLevel(logging.WARNING)
		print("Getting key file")
		self.connect()
		
	def connect(self):
		if self.m_sshHandle != None:
			self.close()
		time_begin = time.time()
		while time.time() - time_begin < self.m_connTimeout and not self.m_isConnected:
			try:
				self.m_sshHandle = paramiko.SSHClient()
			except KeyboardInterrupt as kb_e:
				raise kb_e
			except Exception, e:
				print("could not paramiko.SSHClient(), retrying")
				print(e)
				self.m_sshHandle = None
			else:
				try:
					mykey = paramiko.RSAKey.from_private_key_file(self.m_private_key_file, self.m_key_passphrase)
					print("The key is ready")
					# necessary to avoid exception
					self.m_sshHandle.set_missing_host_key_policy(paramiko.AutoAddPolicy())
					self.m_sshHandle.connect(self.m_sshIP, username=self.m_sshLogin, pkey=mykey, timeout=20)
				except KeyboardInterrupt as kb_e:
					raise kb_e
				except Exception, e:
					self.m_sshHandle = None
					time.sleep(1)
					traceback.print_tb(sys.exc_info()[2])
					print(sys.exc_info())
				else:
					self.m_isConnected = True
				if not self.m_isConnected:
					print("Impossible to connect SSH on address " + self.m_sshIP + " with login " + self.m_sshLogin)
				else:
					try:
						self.m_sshChannel = self.m_sshHandle.invoke_shell(term='dumb', width=80, height=24)
						print("SSH Connection successful")
					except paramiko.ChannelException, e:
						print("ChannelException")
						print(e)
					except KeyboardInterrupt as kb_e:
						raise kb_e
					except Exception, e:
						print("Connection Exception ==> Closing the CHANNEL")
						traceback.print_tb(sys.exc_info()[2])
						print(sys.exc_info())
						self.m_sshChannel = None
						self.m_sshHandle.close()
						self.m_sshHandle = None
						self.m_isConnected = False
		

def parase(text):
	(ritType, ritName,Vendor_unit_type,Vendor_unit_family_type,Vendor_unit_type_name,version_number,serial_number) = ("","","","","","","")
	
	pattern = re.compile(r'.*ritType:   (.*)\n',re.MULTILINE)
	match = pattern.search(text)
	if match:
		ritType = match.group(1).strip().strip(' ')
		#print ritType
	
	pattern = re.compile(r'.*ritName:   (.*)\n',re.MULTILINE)
	match = pattern.search(text)
	if match:
		ritName= match.group(1).strip().strip(' ')
		#print ritName
	
	pattern = re.compile(r'.*Vendor unit type: (.*)\n',re.MULTILINE)
	match = pattern.search(text)
	if match:
		Vendor_unit_type =  match.group(1).strip().strip(' ')
		#print Vendor_unit_type
	
	pattern = re.compile(r'.*Vendor unit family type: (.*)\n',re.MULTILINE)
	match = pattern.search(text)
	if match:
		Vendor_unit_family_type= match.group(1).strip().strip(' ')
		#print Vendor_unit_family_type
	
	pattern = re.compile(r'.*Vendor unit type number: (.*)\n',re.MULTILINE)
	match = pattern.search(text)
	if match:
		Vendor_unit_type_name = match.group(1).strip().strip(' ')
		#print Vendor_unit_type_name
	
	pattern = re.compile(r'.*Version number: (.*)\n',re.MULTILINE)
	match = pattern.search(text)
	if match:
		version_number =  match.group(1).strip().strip(' ')
		#print version_number
	
	pattern = re.compile(r'.*Serial number:  (.*)\n',re.MULTILINE)
	match = pattern.search(text)
	if match:
		serial_number =  match.group(1).strip().strip(' ')
		#print serial_number
		
	return (ritType, ritName,Vendor_unit_type,Vendor_unit_family_type,Vendor_unit_type_name,version_number,serial_number)
	
if __name__ == "__main__":
	# test
	#===========================================================================
	ips = ['10.9.33.118']
	bcis = ["CfgMgrBB-203000/show","CfgMgrCB-101000/show","CfgMgrRRH-1011000/show","CfgMgrRRH-1021000/show","CfgMgrRRH-1031000/show","CfgMgrDBU-21000/show"]
	for ip in ips:
		mySSH = SSH(ip, '22', 'enb0dev', 'Qwe*90op', 120)
		mySSH.expect(["Starting CLI Process"],2)
		mySSH.write("cd /OAM-C/oamctrl")
		[index, match, text] = mySSH.expect(["/OAM-C/oamctrl> "],2)

		for bci in bcis:
			mySSH.write(bci)
			[index, match, text] = mySSH.expect(["/OAM-C/oamctrl> "],2)
			[ritType, ritName,Vendor_unit_type,Vendor_unit_family_type,Vendor_unit_type_name,version_number,serial_number] = parase(text)
			print ip+"	"+ritType+"	"+ritName+'	'+Vendor_unit_type+'	'+Vendor_unit_family_type+'	'+Vendor_unit_type_name+'	'+version_number+'	'+serial_number+'	'

	'''	
	mySSH = SSH('10.9.33.80', '22', 'enb0dev', 'Qwe*90op', 120)
	mySSH.expect(["Starting CLI Process"],2)
	mySSH.write("cd /OAM-C/oamctrl")
	[index, match, text] = mySSH.expect(["/OAM-C/oamctrl> "],2)	
	mySSH.write("cd /pltf/hral")
	[index, match, text] = mySSH.expect(["/pltf/hral\>"],2)
	print(text)
	mySSH.write("ls")
	[index, match, text] = mySSH.expect(["RO BCI Proxy commands"],2)
	print(text)
	remaining = mySSH.read_very_eager()
	print("----")
	print(remaining)
	mySSH.close()
	'''
	#===========================================================================
	
	'''
	s3 = SSH("10.9.33.80",22,"enb0dev","Qwe*90op",5)
	s3.set_current_buffer
	s3.write("ls")
	print s3.read_very_lazy
	
	print("Open SSHKEY connection to a server")
	# key file must be in openssh format
	##############################################################
	# ATTENTION:  this tests works only for my environment  --> by DB !!!
	# build up your own with your keys and a login you have access to
	##############################################################
	mySSH = SSHKEY('172.27.102.35','22', 'modemadm', 'D:\privatekeyOpenSSH.ppk','wireless preint unlocker', 120)
	mySSH.expect(["modemadm@frctfsucc018"],12)
	mySSH.write("cd /swbts/modem1/PREINTEGRATION")
	[index, match, text] = mySSH.expect(["/swbts/modem1/PREINTEGRATION"],12)
	print(text)
	mySSH.write("ls")
	[index, match, text] = mySSH.expect(["install_enbload_on_target"],12)
	print(text)
	remaining = mySSH.read_very_eager()
	print("----")
	print(remaining)
	mySSH.close()
	print("SSHKEY connection CLOSED")
	'''
	
