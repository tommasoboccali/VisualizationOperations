#!/usr/bin/env python
import os,string,sys,commands,time,socket,thread,ConfigParser,signal

#PhysDecl bit check parameters
DIRE="None"


# connection parameters
HOST = 'localhost'    # host where thr program runs runs
PORTSERV = 9005            # receive port
PORTCLIENT = 9006
HOSTREC=''
RECEIVED = 0                # flag for tcpserver thread
DATA = ''                   # the answer
TIMEOUT=600

global s_recv

def signal_handler(signal, frame):
   print 'EVDISPMONSERVER: You pressed Ctrl+C!...closing socket'
   s_recv.close()
   sys.exit(0)


def getspeed():
    x=open('/proc/net/dev','r')
    for line in x.readlines():
        line=line.strip()
        if (line[:4] == 'eth0'):
            line=line[5:].split()
            bin=int(line[0])
            bout=int(line[8])
    return (bin, bout)


def buildans():
   ANS=''
   # network business
   z=getspeed()

   BIN=z[0]
   ANS+="BIN:"+str(z[0])+";"

   BOUT=z[1]
   ANS+="BOUT:"+str(z[1])+";"

   LOGFILE=commands.getoutput("ls -1tr "+DIRE+"/SkimSM*.log | grep -vi second|tail -1")
   PD=commands.getoutput("grep PhysDecl "+LOGFILE+" |grep -i accept| tail -1 | awk '{print $13,$3,$8}'")
   ANS+="PD:"+PD+";"

   LASTLINE=commands.getoutput("tail -1 "+LOGFILE)
   ANS+="LL:"+LASTLINE+";"

   EV_IN=commands.getoutput("grep Begin "+LOGFILE+" | wc -l")
   ANS+="EVIN:"+EV_IN+";"

   EV_OUT=commands.getoutput("grep PhysDecl "+LOGFILE+" | wc -l")
   ANS+="EVOUT:"+EV_OUT+";"

   DCS=commands.getoutput("grep Partitions "+LOGFILE+" | tail -1 | awk -F : '{print $2}'")
   ANS+="DCS:"+DCS+";"

   HLTCFG      =commands.getoutput("head -10 "+LOGFILE+" | grep HLT_selection | awk -F : '{print $2}'")
   TRIGTYPECFG =commands.getoutput("head -10 "+LOGFILE+" | grep Triggertype_selection | awk -F : '{print $2}'")
   L1TECHCFG   =commands.getoutput("head -10 "+LOGFILE+" | grep TechTrigger_selection: | awk -F : '{print $2}'")
   ANS+="HLTSEL:"+HLTCFG+";"
   ANS+="TTSEL:"+TRIGTYPECFG+";"
   ANS+="L1TTSEL:"+L1TECHCFG+";"
   

#   print LOGFILE
   return ANS

def tcpsend(MESSAGE):
   global RECEIVED,TCPIP,HOSTREC
   s_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   # print "Sending to "+HOSTREC+str(PORTCLIENT)
   try:
      s_send.connect((HOSTREC, PORTCLIENT))
      s_send.send(MESSAGE)
   except:
      print "EVDISPMON: Problem in answering "+HOSTREC 
   # print 'TCP Sending '+MESSAGE
   s_send.close()

# function to talk to tcp threshold server
def tcpserver():
    global RECEIVED,LAST_TCPIP_REC,HOSTREC,s_recv
    RECEIVED=0

    SERVERSTARTED=False
    TRIES=0

    # print socket.gethostname(),PORTSERV
    while not SERVERSTARTED and TRIES<TIMEOUT:
       try:
          s_recv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          s_recv.bind((socket.gethostname(),PORTSERV))
          SERVERSTARTED=True
       except:
          print "EVDISPMON: Problem in binding port, waiting 10s and retry...."
          time.sleep(10)
          TRIES+=10

    if TRIES>=TIMEOUT:
       print "EVDISPMON: Tried too many times.....exiting now."
       sys.exit(1)

          
    while True:
        s_recv.listen(1)
        # print 'Server starting and waiting for connections'
        (conn, addr)= s_recv.accept()
        HOSTREC=socket.gethostbyaddr(addr[0])[0]
#        print 'Connected by', HOSTREC
        data = conn.recv(1024)
#        print 'Received:\n', data
        if data=="ASK":
           # here put the answer
           ANS=buildans()
           tcpsend(ANS)
           # print "answered"

    # s_recv.close()
    # print 'Exiting..'
    # RECEIVED=1


# here is the main------------------------------------------------------------
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
if len(sys.argv)!=2:
       print "Usage: "+sys.argv[0]+" LogArea"
       sys.exit(0)
else:
       DIRE=sys.argv[1]


print "Using Area: "+DIRE
tcpserver()
