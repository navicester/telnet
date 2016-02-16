#!/usr/bin/env python
# -*- coding: cp936 -*-

#Episode 

import pexpect
import os
#import basicSetting
#from logger import #LOGGER_ERROR, #LOGGER_DEBUG
#from enbconf import EnbConf
import time
import re

class ssh2:
    def __init__(self,host_name,user_name,password,prompt):
        """
        @param host_name: Host name or IP address
        @param user_name: User name
        @param password: Password

        """

        self.hostname=host_name
        self.username=user_name
        self.password=password
        self.prompt=prompt
        self.tn = None
        self.port=22 ##default SSH port

    def getHostName(self):
        return self.hostname

    def login(self):
        is_login=-1
        ssh_keyChanged = 'Host key verification failed.'
        ssh_newkey = 'Are you sure you want to continue connecting'
        self.ssh = pexpect.spawn('ssh -o StrictHostKeyChecking=no %s@%s' % (self.username,self.hostname), maxread = 99999999)
        i = self.ssh.expect([pexpect.TIMEOUT,pexpect.EOF,ssh_newkey,ssh_keyChanged,'password:'], 5)
        if i == 0: #timeout
            print ("SSH Login(%s): could not login due to timeout!"%self.hostname)
            is_login=-1
            pass
        if i == 1:
            print ('SSH Login(%s):'%self.hostname + self.ssh.before)
            if re.search('.*(REMOTE HOST IDENTIFICATION HAS CHANGED!).*',self.ssh.before,re.MULTILINE):
                status = os.system('ssh-keygen -R ' + self.hostname)
                if status ==0:
                    is_login = self.login()
                else:
                    print ('ssh-keygen failed! %s'%self.hostname)    
                    pass            
            else:
                is_login=-1
                pass
        if i == 2:
            #ssh does not have the public key.Just accecpt it.
            self.ssh.sendline('yes')
            i2=self.ssh.expect([pexpect.TIMEOUT,pexpect.EOF,'password:'])
            if i2==0: #timeout
                print ("SSH Login(%s):  could not login due to timeout!"%self.hostname)
                is_login=-1
                pass
            if i2==1:
                print ("SSH Login(%s):"%self.hostname+self.ssh.before)
                is_login=-1
                pass
            if i2==2:
                self.ssh.sendline(self.password)
                is_login=1
                pass

        if i==3:
            #The RSA host key changed
            status = os.system('ssh-keygen -R ' + self.hostname)
            if status !=0:
                print ('ssh-keygen failed! %s'%self.hostname)
                pass
            #self.ssh.sendline('ssh-keygen -R ' + self.hostname)
            #clearResult = self.ssh.expect([pexpect.TIMEOUT,pexpect.EOF,self.prompt])
            self.ssh.close()
            is_login = self.login()
            pass
        if i==4:
            self.ssh.sendline(self.password)
            i4=self.ssh.expect([pexpect.TIMEOUT,pexpect.EOF,self.prompt])
            if i4==0: #timeout
                print ("SSH Login(%s):  could not login due to timeout!"%self.hostname)
                is_login=-1
                pass
            if i4==1: #eof
                print ('SSH Login(%s): '%self.hostname + self.ssh.before)
                is_login=-1
                pass
            if i4==2: #successfully
                is_login=1
                print "successfully"
                pass
        return is_login

    def cemsshlogin(self, cemid):
        ssh_keyChanged  = 'Host key verification failed.'
        ssh_newkey      = 'Are you sure you want to continue connecting'
        self.ssh.sendline('ssh %s@%s' % (self.username, '192.168.%d.1' % (cemid + 1)))

        i = self.ssh.expect([pexpect.TIMEOUT, pexpect.EOF, ssh_newkey, ssh_keyChanged, 'password:'], 10)
        if i == 0: #TIMEOUT
            ##LOGGER_ERROR('failed: timeout, CEM SSH Login(%s, %d):' % (self.hostname, cemid) + self.ssh.before)
            return False
        elif i == 1: #EOF
            #LOGGER_ERROR('failed: CEM SSH Login(%s, %d):' % (self.hostname, cemid) + self.ssh.before)
            return False
        elif i == 2: #new key
            self.ssh.sendline('yes')
            i2 = self.ssh.expect([pexpect.TIMEOUT, pexpect.EOF, 'password:'])
            if i2 == 0: #timeout
                #LOGGER_ERROR('failed: CEM SSH Login(%s, %d):' % (self.hostname, cemid) + self.ssh.before)
                return False
            if i2 == 1: #EOF
                #LOGGER_ERROR('failed: CEM SSH Login(%s, %d):' % (self.hostname, cemid) + self.ssh.before)
                return False
            if i2 == 2:
                self.ssh.sendline(self.password)
        elif i==3: #key change
            self.ssh.sendline('ssh-keygen -R ' + '192.168.%d.1' % (cemid + 1))
            return self.cemsshlogin(cemid)
        elif i==4:
            self.ssh.sendline(self.password)
            i4 = self.ssh.expect([pexpect.TIMEOUT, pexpect.EOF, self.prompt])
            if i4 == 0: #timeout
                #LOGGER_ERROR('failed: CEM SSH Login(%s, %d):' % (self.hostname, cemid) + self.ssh.before)
                return False
            if i4 == 1: #eof
                #LOGGER_ERROR('failed: CEM SSH Login(%s, %d):' % (self.hostname, cemid) + self.ssh.before)
                return False
            if i4 == 2: #successfully
                pass

        if not self.run_command('sh')[0]:
            #LOGGER_ERROR('failed: CEM SSH Login(%s, %d):' % (self.hostname, cemid) + self.ssh.before)
            return False
        if not self.run_command('su', 'Password:')[0]:
            #LOGGER_ERROR('failed: CEM SSH Login(%s, %d):' % (self.hostname, cemid) + self.ssh.before)
            return False
        if not self.run_command('#edcVfr4%t')[0]:
            #LOGGER_ERROR('failed: CEM SSH Login(%s, %d):' % (self.hostname, cemid) + self.ssh.before)
            return False
        if not self.run_command('cd /root', 'root-/root>')[0]:
            #LOGGER_ERROR('failed: CEM SSH Login(%s, %d):' % (self.hostname, cemid) + self.ssh.before)
            return False
        return True

    def is_rightprompt(self,prompt):
        is_prompt=False
        if prompt:
            self.ssh.expect(prompt)
            is_prompt=True
        return is_prompt

    def telnetCEM(self, ip):
        command = 'telnet ' + ip
        self.ssh.sendline(command)
        i = self.ssh.expect(['login:', pexpect.TIMEOUT, pexpect.EOF], 10)
        if i == 0:
            resp = self.ssh.before
            resp = resp.replace(command,'').strip()
            return True, resp
        elif i==1:
            return False, self.ssh.before
        else:
            #LOGGER_ERROR("SSH command:%s cann't execute due to EOF! platform: %s" % (command, self.hostname))
            return False, self.ssh.before


    def run_command(self,command,prompt = '>', timeout = -1):
        time.sleep(2)
        """Run a command on the remote host.

        @param command: Unix command
        @return: Command output
        @rtype: String
        """
        status=1
        self.ssh.sendline(command)
        i=self.ssh.expect([prompt,pexpect.TIMEOUT,pexpect.EOF], timeout)
        if i==0:
            resp=self.ssh.before
            resp=resp.replace(command,'').strip()
        elif i==1:
            #LOGGER_ERROR("SSH command:%s cann't execute due to timeout! platform: %s" % (command, self.hostname))
            status=0
            resp=self.ssh.before
        elif i==2:
            #LOGGER_ERROR("SSH command:%s cann't execute due to EOF!"%command)
            status=0
            resp=self.ssh.before
        #if self.hostname == "10.9.35.225":
            ##LOGGER_DEBUG('testtesttest')
            ##LOGGER_DEBUG(self.ssh)
        return status,resp

    def run_commandnoenter(self,command,prompt):
        status=1
        self.ssh.send(command)
        i=self.ssh.expect([prompt,pexpect.TIMEOUT,pexpect.EOF])
        if i==0:
            resp=self.ssh.before
            resp=resp.replace(command,'').strip()
        elif i==1:
            #LOGGER_ERROR("SSH command:%s cann't execute due to timeout!"%command)
            status=0
            resp=self.ssh.before
        elif i==2:
            #LOGGER_ERROR("SSH command:%s cann't execute due to EOF!"%command)
            status=0
            resp=self.ssh.before
        return status,resp

    def run_command2(self,command,prompt1,prompt2):
        status=-1
        self.ssh.sendline(command)
        i=self.ssh.expect([prompt1,prompt2,pexpect.TIMEOUT,pexpect.EOF])
        if i==0:
            resp=self.ssh.before
            resp=resp.replace(command,'').strip()
            status=0
        elif i==1:
            resp=self.ssh.before
            resp=resp.replace(command,'').strip()
            status=1
        elif i==2:
            #LOGGER_ERROR("SSH command:%s cann't execute due to timeout!"%command)
            resp=self.ssh.before
            status=2
        elif i==3:
            #LOGGER_ERROR("SSH command:%s cann't execute due to EOF!"%command)
            resp=self.ssh.before
            status=3
        return status,resp

    def run_command2noenter(self,command,prompt1,prompt2):
        status=-1
        self.ssh.send(command)
        i=self.ssh.expect([prompt1,prompt2,pexpect.TIMEOUT,pexpect.EOF])
        if i==0:
            resp=self.ssh.before
            resp=resp.replace(command,'').strip()
            status=0
        elif i==1:
            resp=self.ssh.before
            resp=resp.replace(command,'').strip()
            status=1
        elif i==2:
            #LOGGER_ERROR("SSH command:%s cann't execute due to timeout!"%command)
            resp=self.ssh.before
            status=2
        elif i==3:
            #LOGGER_ERROR("SSH command:%s cann't execute due to EOF!"%command)
            resp=self.ssh.before
            status=3
        return status,resp


    def downloadexpect(self):
        #??self.ssh.sendline(basicSetting.HOST_SERVER_PWD)
        i = self.ssh.expect([pexpect.TIMEOUT, pexpect.EOF, '>'], 120)
        if i == 0:
            #LOGGER_ERROR("download time out, platform: %s", self.getHostName())
            return False
        elif i == 1:
            #LOGGER_ERROR("download error, platform: %s", self.getHostName())
            return False
        elif i == 2:
            return True

    def download_file(self,command):
        status=1

        self.ssh.sendline(command)
        i=self.ssh.expect([pexpect.TIMEOUT,pexpect.EOF,"Are you sure you want to continue connecting (yes/no)?","password:"], 120)
        if i==0:
            status = 0
            #LOGGER_ERROR("SSH command:%s cann't execute due to timeout!"%command)
        elif i==1:
            status = 0
            #LOGGER_ERROR("SSH command:%s cann't execute due to EOF!"%command)
        elif i==2:
            self.ssh.sendline('yes')
            i=self.ssh.expect([pexpect.TIMEOUT,pexpect.EOF,'password:'])
            if i==0:
                status = 0
                #LOGGER_ERROR("SSH command:download file cann't execute due to timeout!, resp : %s" % self.ssh.before)
            elif i==1:
                status = 0
                #LOGGER_ERROR("SSH command:download file cann't execute due to EOF!")
            elif i==2:
                return self.downloadexpect()
        elif i==3:
            return self.downloadexpect()

        return status

    def ftppass(self):
        #??self.ssh.sendline("%s" % EnbConf.LR13_FTP_PASS)
        i = self.ssh.expect([pexpect.TIMEOUT, pexpect.EOF, "sftp>"])
        if i == 0:
            #LOGGER_ERROR('sftp timeout, platform ip: %s' % ip)
            return False
        elif i == 1:
            #LOGGER_ERROR('stfp error, platform ip: %s' % ip)
            return False
        elif i == 2:
            return True

    def ftplogin(self, ip, release):
        if release != 'LR13':
            #??return self.run_ftp(ip, EnbConf.CEM_FTP_USER, EnbConf.CEM_FTP_PWD)
            pass

        ssh_keyChanged = 'Host key verification failed.'
        ssh_newkey = 'Are you sure you want to continue connecting'

        #??self.ssh.sendline('sftp %s@%s' % (EnbConf.LR13_FTP_USER, ip))
        i = self.ssh.expect([pexpect.TIMEOUT, pexpect.EOF, 'password:', ssh_newkey, ssh_keyChanged])
        if i == 0:
            #LOGGER_ERROR('sftp timeout, platform ip: %s' % ip)
            return False
        elif i == 1:
            #LOGGER_ERROR('stfp error, platform ip: %s' % ip)
            return False
        elif i == 2:
            return self.ftppass()
        elif i == 3:
            self.ssh.sendline('yes')
            i = self.ssh.expect([pexpect.TIMEOUT, pexpect.EOF, 'password:'])
            if i == 0: #timeout
                #LOGGER_ERROR('sftp timeout, platform ip: %s' % ip)
                return False
            if i == 1:
                #LOGGER_ERROR('stfp error, platform ip: %s' % ip)
                return False
            if i == 2:
                return self.ftppass()
        elif i == 4:
            self.ssh.sendline('ssh-keygen -R ' + ip)
            return self.ftplogin(ip, release)

    def run_ftp(self,ip,user,password):
        status=0
        self.ssh.sendline("ftp %s"%ip)
        i=self.ssh.expect([pexpect.TIMEOUT,pexpect.EOF,"Login for '%s':"%ip])
        if i==0:
            #LOGGER_ERROR("SSH command:ftp cann't execute due to timeout!")
            pass
        elif i==1:
            #LOGGER_ERROR("SSH command:ftp cann't execute due to EOF!")
            pass
        elif i==2:
            self.ssh.sendline("%s"%user)
            i=self.ssh.expect([pexpect.TIMEOUT,pexpect.EOF,"Password for '%s@%s':"%(user,ip)])
            if i==0:
                #LOGGER_ERROR("SSH command:ftp login cann't execute due to timeout!")
                pass
            elif i==1:
                #LOGGER_ERROR("SSH command:ftp login cann't execute due to EOF!")
                pass
            elif i==2:
                self.ssh.sendline("%s"%password)
                i=self.ssh.expect([pexpect.TIMEOUT,pexpect.EOF,"%s@%s:21>"%(user,ip)])
                if i==0:
                    #LOGGER_ERROR("SSH command:ftp password cann't execute due to timeout!")
                    pass
                elif i==1:
                    #LOGGER_ERROR("SSH command:ftp password cann't execute due to EOF!")
                    pass
                elif i==2:
                    status=1
        return status

    def run_telnet(self,ipaddr,prompt):
        status=1
        try:
            self.run_command('telnet %s'%ipaddr,'login:')
            #??self.run_command(basicSetting.ENB_CEM_USER,'assword')
            #??self.run_command(basicSetting.ENB_CEM_PWD,prompt)
        except pexpect.TIMEOUT or pexpect.EOF:
            #LOGGER_ERROR("SSH Command:telnet failure to %s due to timeout or EOF!"%ipaddr)
            status=0
        return status

    def expect(self,command):
        is_expected=False
        if self.ssh.expect(command):
            is_expected=True
        return is_expected

    def logout(self):
        try:
            self.ssh.close()
        except:
            #LOGGER_ERROR("ssh close failed %s"% self.hostname)
            pass

    def __strip_output(self, command, response):
        """Strip everything from the response except the actual command output.

        @param command: Unix command
        @param response: Command output
        @return: Stripped output
        @rtype: String
        """
        lines = response.splitlines()
        # if our command was echoed back, remove it from the output
        if command in lines[0]:
            lines.pop(0)
        # remove the last element, which is the prompt being displayed again
        lines.pop()
        # append a newline to each line of output
        lines = [item + '\n' for item in lines]
        # join the list back into a string and return it
        return ''.join(lines)

class telnet:
    def __init__(self,ip,username,password,prompt):
        self.ip=ip
        self.username=username
        self.password=password
        self.prompt=prompt

    def login(self):
        status=0
        self.session=pexpect.spawn('telnet %s'%(self.ip))
        i=self.session.expect([pexpect.TIMEOUT,pexpect.EOF,'Do you want to send anyway(y/n):','login:'], 60)
        if i==0:
            #LOGGER_ERROR('Telnet could not login due to timeout')
            pass
        elif i==1:
            #LOGGER_ERROR('Telnet could not login due to eof')
            pass
        elif i==2:
            self.session.send('n\r')
            i=self.session.expect([pexpect.TIMEOUT,pexpect.EOF,'login:'])
            if i==0:
                #LOGGER_ERROR('Telnet could not login due to timeout')
                pass
            elif i==1:
                #LOGGER_ERROR('Telnet could not login due to eof')
                pass
            elif i==2:
                self.session.send('%s\r'%(self.username))
                i=self.session.expect([pexpect.TIMEOUT,pexpect.EOF,'password:'])
                if i==0:
                    #LOGGER_ERROR('Telnet could not login due to timeout')
                    pass
                elif i==1:
                    #LOGGER_ERROR('Telnet could not login due to eof')
                    pass
                elif i==2:
                    self.session.send('%s\r'%(self.password))
                    i=self.session.expect([pexpect.TIMEOUT,pexpect.EOF,self.prompt])
                    if i==0:
                        #LOGGER_ERROR('Telnet could not login due to timeout')
                        pass
                    elif i==1:
                        #LOGGER_ERROR('Telnet could not login due to eof')
                        pass
                    elif i==2:
                        status=1
        elif i==3:
            self.session.send('%s\r'%(self.username))
            i=self.session.expect([pexpect.TIMEOUT,pexpect.EOF,'password:'])
            if i==0:
                #LOGGER_ERROR('Telnet could not login due to timeout')
                pass
            elif i==1:
                #LOGGER_ERROR('Telnet could not login due to eof')
                pass
            elif i==2:
                self.session.send('%s\r'%(self.password))
                i=self.session.expect([pexpect.TIMEOUT,pexpect.EOF,self.prompt])
                if i==0:
                    #LOGGER_ERROR('Telnet could not login due to timeout')
                    pass
                elif i==1:
                    #LOGGER_ERROR('Telnet could not login due to eof')
                    pass
                elif i==2:
                    status=1
        return status

    def run_command(self,command,prompt):
        status=0
        resp=''
        self.session.send('%s\r'%command)
        i=self.session.expect([pexpect.TIMEOUT,pexpect.EOF,prompt])
        if i==0:
            #LOGGER_ERROR('Telnet command:%s could not execute due to timeout'%command)
            pass
        elif i==1:
            #LOGGER_ERROR('Telnet command:%s could not execute due to eof'%command)
            pass
        elif i==2:
            status=1
            resp=self.session.before
            resp=resp.replace(command,'').strip()
        return status,resp

    def logout(self):
        self.session.close()


if __name__ == "__main__":
    sshClient = ssh2("10.9.35.72","enb0dev","Qwe*90op", ">")
    sshClient.login();
