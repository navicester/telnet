# -*- coding: utf-8 -*-   


import telnetlib  
import time
  
# ����ѡ��  
Host = '135.251.227.17' # Telnet������IP  
port = 23
username = 'bhe001'   # ��¼�û���  
password = '123'  # ��¼����  
finish = '~]$ '      # ������ʾ������ʶ����һ��������ִ����ϣ�  
test_commands = ['ls','ifconfig']
enter_key = "\r\n"
delay_sec = 1

# ����Telnet������  

cur_time = time.localtime()
log_file_name = "monitor_" + str(cur_time[0]) + "_" + \
                             str(cur_time[1]) + "_" + \
                             str(cur_time[2]) + "_" + \
                             str(cur_time[3]) + "_" + \
                             str(cur_time[4]) + "_" + \
                             str(cur_time[5]) + ".log"

log_file = open(log_file_name, "w")
log_file.write("IP: " + Host + "\n")
log_file.write("Port: %s" % port + "\n")

tn = telnetlib.Telnet(Host,port=23,timeout=10)  

# �����¼�û���  
tn.read_until('login:')  
tn.write(username + '\n')  
  
# �����¼����  
tn.read_until('Password:')  
tn.write(password + '\n')  

# ��¼��Ϻ�ִ��ls����  
tn.read_until(finish)  
tn.write('ls\n')  

for command in test_commands:  
    tn.write('%s\n' % command)  
    recv = tn.read_very_eager()
    #print recv
    
while(1):
    t = raw_input("")
    #print t
    tn.write('%s' % t + enter_key)
    #time.sleep(delay_sec)  
    recv = tn.read_very_eager()
    print recv + enter_key
    log_file.write(recv)
    log_file.flush()
          
# ls����ִ����Ϻ���ֹTelnet���ӣ�������exit�˳���  
tn.read_until(finish)  
tn.close() # tn.write('exit\n')  
log_file.close()

def do_telnet(Host, username, password, finish, commands):  

    tn = telnetlib.Telnet(Host, port=23, timeout=10)  
    tn.set_debuglevel(2)  
       
    # �����¼�û���  
    tn.read_until('login: ')  
    tn.write(username + '\n')  
      
    # �����¼����  
    tn.read_until('Password: ')  
    tn.write(password + '\n')  
        
    # ��¼��Ϻ�ִ������  
    tn.read_until(finish)  

    for command in commands:  
        tn.write('%s\n' % command)  
        recv = tn.read_very_eager()
        print recv
        
    tn.read_until(finish)  
    tn.close() # tn.write('exit\n')  
    
if __name__=='__main__':    
    Host = '192.168.1.1' 
    username = 'gpon'   
    password = 'gpon'  
    finish = '~]$ '            
    
    tn = telnetlib.Telnet(Host,port=23,timeout=10)  
    
    tn.read_until('login:')  
    tn.write(username + '\n')  
       
    tn.read_until('Password:')  
    tn.write(password + '\n')  
    
    tn.read_until(finish)  
    tn.write('ls\n')  
      
    tn.read_until(finish)  
    tn.close() # tn.write('exit\n')  

