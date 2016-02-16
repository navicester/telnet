

#encoding=utf-8  
# my practice

import telnetlib  
import paramiko
import sys
import time
#
#import pexpect
from sshLib import SSH

class myssh2:
    def __init__(self,hostname="10.9.33.80", username="enb0dev", password="Qwe*90op",prompt=''):
        """
        @param host_name: Host name or IP address
        @param user_name: User name
        @param password: Password

        """

        self.hostname=hostname
        self.username=username
        self.password=password
        self.prompt=prompt
        self.tn = None
        self.port=22 ##default SSH port
        
    def telnet(self):  
        #pkey='E:/PythonWeb/ssh_host_rsa_key'
        #key=paramiko.RSAKey.from_private_key_file(pkey,password=password)
        
        paramiko.util.log_to_file('paramiko.log')   #通过公共方式进行认证 (不需要在known_hosts 文件中存在) ~/.ssh/known_hosts
        s=paramiko.SSHClient()
        #s.load_system_host_keys()  #如通过known_hosts 方式进行认证可以用这个,如果known_hosts 文件未定义还需要定义 known_hosts  
        s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #print s.connect(hostname=hostname,port=22,username=username,password=password,timeout=5,pkey=key) #这里要 pkey passwordkey 密钥文件 
        s.connect(hostname=self.hostname,port=self.port,username=self.username,password=self.password,timeout=5,look_for_keys=False,allow_agent=False)
        
        #s.read_until("Starting CLI Process")  
        time.sleep(10)
        
        stdin,stdout,stderr=s.exec_command('ls')
        #print stdout.read()
        for line in stdout.read().splitlines():  
            print line  
        print stdout.readlines()        
        s.close()    
        
    def telnet2(self):  
        
        #pkey='E:/PythonWeb/ssh_host_rsa_key'
        #key=paramiko.RSAKey.from_private_key_file(pkey,password=password)
        
        paramiko.util.log_to_file('paramiko.log')   #通过公共方式进行认证 (不需要在known_hosts 文件中存在) ~/.ssh/known_hosts
        s=paramiko.SSHClient()
        #s.load_system_host_keys()  #如通过known_hosts 方式进行认证可以用这个,如果known_hosts 文件未定义还需要定义 known_hosts  
        s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        s.connect(hostname=self.hostname,port=self.port,username=self.username,password=self.password,timeout=5)
        
        
        while True:  
            cmd = raw_input("Please Input Command to run in server %s : " %(hostname))  
            if cmd == "":  
                break  
            
            channel = s.get_transport().open_session()  
            print "running '%s'" % cmd  
            channel.exec_command(cmd)  
            print "exit status: %s" % channel.recv_exit_status()  
            print "exit status: %s" % channel.recv(10000)
            
        s.close()
    
    def telnet3(self,Host, username, password, finish, commands):  
        
        nbytes = 4096
        command = 'ls'
        
        client = paramiko.Transport((hostname, port))
        client.connect(username=username, password=password)
        
        stdout_data = []
        stderr_data = []
        session = client.open_channel(kind='session')
        session.exec_command(command)
        while True:
            if session.recv_ready():
                stdout_data.append(session.recv(nbytes))
            if session.recv_stderr_ready():
                stderr_data.append(session.recv_stderr(nbytes))
            if session.exit_status_ready():
                break
        
        print 'exit status: ', session.recv_exit_status()
        print ''.join(stdout_data)
        print ''.join(stderr_data)
        
        session.close()
        client.close()
                
if __name__=='__main__':  

    Host = '192.168.128.132' # Telnet������IP  
    username = 'bhe001'   # ��¼�û���  
    password = '123'  # ��¼����  
    finish = '~]$ '      # ������ʾ��  
    commands = ['ls', 'ifconfig' ]  
    #do_telnet(Host, username, password, finish, commands)  
    
    hostname='10.9.45.89'
    username='enb0dev'
    password='Qwe*90op'
    
    username='enb3operator'
    password='uyTPoi@#'
    port = 22    

    hostname='10.9.33.80'
    username='root'
    password='asb#1234' 
    
    username='enb0dev'
    password='Qwe*90op' 
    
    '''
    from ssh2 import ssh2
    s2 = ssh2(hostname,username,password,"")
    s2.login()
    #status,res=s2.run_commandnoenter("ls",">")
    #print res
    status,res=s2.run_command("ls",">")
    print res
    '''
    
    Myssh2 = myssh2(hostname,username,password)
    Myssh2.telnet()
    
    #s3 = SSH(hostname,22,username,password,5)
    