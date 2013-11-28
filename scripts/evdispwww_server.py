#!/usr/bin/env python
import os,string,sys,commands,time,socket,thread,ConfigParser,signal

global s_recv,ANS,LOCK,HTMLTEMPLATE,HTMLFILE,DIRE

#PhysDecl bit check parameters
DIRE="None"
HTMLFILE="/afs/cern.ch/user/m/malgeril/www/evdispmon/evdispmon.html"

# connection parameters
HOST = 'localhost'    # host where thr program runs runs
PORTSERV = 9005            # receive port
#lmtest
PORTSERV = 9004            # receive port
PORTCLIENT = 9006
HOSTREC=''
RECEIVED = 0                # flag for tcpserver thread
DATA = ''                   # the answer
TIMEOUT=600

ANS=""
LOCK=True




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
   global ANS,LOCK,HTMLFILE,HTMLTEMPLATE,DIRE
   lasttime=1
   lastin=0.
   lastout=0.
   lastevin=0
   lastevout=0

   while True:
      LOCK=True
      LAST=time.ctime()
      
      timedelta=time.time()-lasttime
      lasttime=time.time()

      ANS="LAST:"+LAST.replace(":","-")+";"
   # netowrk socket part   
   # network business
      try:
#      if (True):
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
         
         EV_OUT=commands.getoutput("grep Decl "+LOGFILE+" | wc -l")
         ANS+="EVOUT:"+EV_OUT+";"
         
         DCS=commands.getoutput("grep Partitions "+LOGFILE+" | tail -1 | awk -F : '{print $2}'")
         ANS+="DCS:"+DCS+";"
         
         HLTCFG      =commands.getoutput("head -10 "+LOGFILE+" | grep HLT_selection | awk -F : '{print $2}'")
         TRIGTYPECFG =commands.getoutput("head -10 "+LOGFILE+" | grep Triggertype_selection | awk -F : '{print $2}'")
         L1TECHCFG   =commands.getoutput("head -10 "+LOGFILE+" | grep TechTrigger_selection: | awk -F : '{print $2}'")
#         print LOGFILE
#         print "HLTCFG=",HLTCFG
#         print "tt CFG=",TRIGTYPECFG
#         print "l1 CFG=",L1TECHCFG

         ANS+="HLTSEL:"+HLTCFG+";"
         ANS+="TTSEL:"+TRIGTYPECFG+";"
         ANS+="L1TTSEL:"+L1TECHCFG+";"
         
         sin=(float(BIN)-lastin)/(1024*timedelta)
         ANS+="NETIN:"+"%.2f"%(sin)+";"
         lastin=float(BIN)
         
         sout=(float(BOUT)-lastout)/(1024*timedelta)
         ANS+="NETOUT:"+"%.2f"%(sout)+";"
         lastout=float(BOUT)
         
         if EV_IN.isdigit():
            rate_in=(float(EV_IN)-lastevin)/(timedelta)
            lastevin=float(EV_IN)
         else:
            rate_in=0
         ANS+="RATEIN:"+"%.2f"%(rate_in)+";"
         
         if EV_OUT.isdigit():
            rate_out=(float(EV_OUT)-lastevout)/(timedelta)
            lastevout=float(EV_OUT)
         else:
            rate_out=0
         ANS+="RATEOUT:"+"%.2f"%(rate_out)+";"

#############################################################
         # create html file
#############################################################

         HTMLPAGE=HTMLTEMPLATE
         HTMLPAGE=HTMLPAGE.replace("TAG_DATE",LAST)
         HTMLPAGE=HTMLPAGE.replace("TAG_NETIN","%.2f"%(sin))
         if sin<0.01:
            HTMLPAGE=HTMLPAGE.replace("COL_NETIN","red")
         else:
            HTMLPAGE=HTMLPAGE.replace("COL_NETIN","green")

         HTMLPAGE=HTMLPAGE.replace("TAG_NETOUT","%.2f"%(sout))
         if sout<0.01:
            HTMLPAGE=HTMLPAGE.replace("COL_NETOUT","red")
         else:
            HTMLPAGE=HTMLPAGE.replace("COL_NETOUT","green")

         HTMLPAGE=HTMLPAGE.replace("TAG_EVRATEIN","%.2f"%(rate_in))
         if rate_in<0.01:
            HTMLPAGE=HTMLPAGE.replace("COL_EVRATEIN","red")
         else:
            HTMLPAGE=HTMLPAGE.replace("COL_EVRATEIN","green")

         HTMLPAGE=HTMLPAGE.replace("TAG_EVRATEOUT","%.2f"%(rate_out))
         if rate_out<0.01:
            HTMLPAGE=HTMLPAGE.replace("COL_EVRATEOUT","red")
         else:
            HTMLPAGE=HTMLPAGE.replace("COL_EVRATEOUT","green")

         if EV_IN.isdigit():
            HTMLPAGE=HTMLPAGE.replace("TAG_EVIN",EV_IN)
            if int(EV_IN)==0:
               HTMLPAGE=HTMLPAGE.replace("COL_EVIN","red")
            else:
               HTMLPAGE=HTMLPAGE.replace("COL_EVIN","green")
         else:
            HTMLPAGE=HTMLPAGE.replace("TAG_EVIN","None")
            HTMLPAGE=HTMLPAGE.replace("COL_EVIN","blue")

            
         if EV_OUT.isdigit():
            HTMLPAGE=HTMLPAGE.replace("TAG_EVOUT",EV_OUT)
            if int(EV_OUT)==0:
               HTMLPAGE=HTMLPAGE.replace("COL_EVOUT","red")
            else:
               HTMLPAGE=HTMLPAGE.replace("COL_EVOUT","green")
         else:
            HTMLPAGE=HTMLPAGE.replace("TAG_EVOUT","None")
            HTMLPAGE=HTMLPAGE.replace("COL_EVOUT","blue")


         pdsplit=string.split(PD)
         if len(pdsplit)==3:
            curr_run=pdsplit[1]
            curr_ls=pdsplit[2]
            curr_pd=pdsplit[0]
         else:
            curr_run='N/A'
            curr_ls='N/A'
            curr_pd='N/A'
            
         HTMLPAGE=HTMLPAGE.replace("TAG_RUN",curr_run)
         if curr_run=="N/A":
            HTMLPAGE=HTMLPAGE.replace("COL_RUN","blue")
         else:
            HTMLPAGE=HTMLPAGE.replace("COL_RUN","green")

         HTMLPAGE=HTMLPAGE.replace("TAG_LS",curr_ls)
         if curr_ls=="N/A":
            HTMLPAGE=HTMLPAGE.replace("COL_LS","blue")
         else:
            HTMLPAGE=HTMLPAGE.replace("COL_LS","green")

         HTMLPAGE=HTMLPAGE.replace("TAG_PHYSDECL",curr_pd)
         if curr_pd=="N/A":
            HTMLPAGE=HTMLPAGE.replace("COL_PHYSDECL","blue")
         elif int(curr_pd)==1:
            HTMLPAGE=HTMLPAGE.replace("COL_PHYSDECL","green")
         else:
            HTMLPAGE=HTMLPAGE.replace("COL_PHYSDECL","red")

         if len(DCS)>1:
            HTMLPAGE=HTMLPAGE.replace("TAG_DCS",DCS)
            if "None" in DCS:
               HTMLPAGE=HTMLPAGE.replace("COL_DCS","red")
            else:
               HTMLPAGE=HTMLPAGE.replace("COL_DCS","green")
         else:
            HTMLPAGE=HTMLPAGE.replace("TAG_DCS","N/A")
            HTMLPAGE=HTMLPAGE.replace("COL_DCS","blue")
         
         if len(HLTCFG)>1:
            HTMLPAGE=HTMLPAGE.replace("TAG_HLTSEL",HLTCFG)
            if "None" in HLTCFG:
               HTMLPAGE=HTMLPAGE.replace("COL_HLTSEL","red")
            else:
               HTMLPAGE=HTMLPAGE.replace("COL_HLTSEL","green")
         else:
            HTMLPAGE=HTMLPAGE.replace("TAG_HLTSEL","N/A")
            HTMLPAGE=HTMLPAGE.replace("COL_HLTSEL","blue")


         if len(TRIGTYPECFG)>1:
            HTMLPAGE=HTMLPAGE.replace("TAG_TRIGTYPE",TRIGTYPECFG)
            if "None" in TRIGTYPECFG:
               HTMLPAGE=HTMLPAGE.replace("COL_TRIGTYPE","red")
            else:
               HTMLPAGE=HTMLPAGE.replace("COL_TRIGTYPE","green")
         else:
            HTMLPAGE=HTMLPAGE.replace("TAG_TRIGTYPE","N/A")
            HTMLPAGE=HTMLPAGE.replace("COL_TRIGTYPE","blue")


         if len(L1TECHCFG)>1:
            HTMLPAGE=HTMLPAGE.replace("TAG_L1TT",L1TECHCFG)
            if "None" in L1TECHCFG:
               HTMLPAGE=HTMLPAGE.replace("COL_L1TT","red")
            else:
               HTMLPAGE=HTMLPAGE.replace("COL_L1TT","green")
         else:
            HTMLPAGE=HTMLPAGE.replace("TAG_L1TT","N/A")
            HTMLPAGE=HTMLPAGE.replace("COL_L1TT","blue")

         html=open(HTMLFILE,"w")
         html.write(HTMLPAGE)
         html.close()
#         print "html written: ",HTMLFILE

      except:
         pass
            
   #   print LOGFILE
      LOCK=False
#      print ANS
      time.sleep(5)
#      return ANS
   
def tcpsend(MESSAGE):
   global RECEIVED,TCPIP,HOSTREC
   s_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   # print "Sending to "+HOSTREC+str(PORTCLIENT)
   try:
      s_send.connect((HOSTREC, PORTCLIENT))
      s_send.send(MESSAGE)
   except:
      print "EVDISPMON: Problem in answering "+HOSTREC 
#   print 'TCP Sending '+MESSAGE
   s_send.close()

# function to talk to tcp threshold server
def tcpserver():
    global RECEIVED,LAST_TCPIP_REC,HOSTREC,s_recv,LOCK
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
       try:
          s_recv.listen(1)
        # print 'Server starting and waiting for connections'
          (conn, addr)= s_recv.accept()
          HOSTREC=socket.gethostbyaddr(addr[0])[0]
#          print 'Connected by', HOSTREC
          data = conn.recv(4096)
#          print 'Received:\n', data
          if data=="ASK":
             # ANS=buildans()
             # wait unlocked answer
             while LOCK:
                time.sleep(0.1)
             tcpsend(ANS)
       except:
          time.sleep(1)
# print "answered"

             # s_recv.close()
             # print 'Exiting..'
             # RECEIVED=1


# here is the main------------------------------------------------------------
def main():
   global DIRE
   signal.signal(signal.SIGINT, signal_handler)
   signal.signal(signal.SIGTERM, signal_handler)
   if len(sys.argv)!=2:
          print "Usage: "+sys.argv[0]+" LogArea"
          sys.exit(0)
   else:
          DIRE=sys.argv[1]
   
   
   print "Using Area: "+DIRE
   # define html template
   define_template()
   thread.start_new_thread(buildans,())
   tcpserver()


def define_template():
   global HTMLTEMPLATE
   HTMLTEMPLATE="""
<html>
<head>
<META HTTP-EQUIV=REFRESH CONTENT=5>
<meta content="text/html; charset=ISO-8859-1"
http-equiv="content-type">
<title>evdispmon_template</title>
</head>
<body>
<h1 style="color: red;">CMS Event Display Monitoring</h1>
<br>
Last checked time: TAG_DATE<br>
<br>
<table style="text-align: left; width: 448px;" border="1"
cellpadding="2" cellspacing="2">
<tbody>
<tr>
<td style="vertical-align: top; width: 113px;"><br>
</td>
<td style="vertical-align: top; width: 150px;">IN<br>
</td>
<td style="vertical-align: top; width: 119px;">OUT<br>
</td>
<td style="vertical-align: top; width: 45px;"><br>
</td>
</tr>
<tr>
<td style="vertical-align: top; width: 113px;">Network<br>
</td>
<td style="vertical-align: top; width: 150px;">
<span style="color: COL_NETIN;">TAG_NETIN</span><br>
</td>
<td style="vertical-align: top; width: 119px;">
<span style="color: COL_NETOUT;">TAG_NETOUT</span><br>
</td>
<td style="vertical-align: top; width: 45px;">kB/s<br>
</td>
</tr>
<tr>
<td style="vertical-align: top; width: 113px;">Ev rate<br>
</td>
<td
style="vertical-align: top; width: 150px;">
<span style="color: COL_EVRATEIN;">TAG_EVRATEIN</span><br>
</td>
<td style="vertical-align: top; width: 119px;">
<span style="color: COL_EVRATEOUT;">TAG_EVRATEOUT</span><br>
</td>
<td style="vertical-align: top; width: 45px;">ev/s<br>
</td>
</tr>
<tr>
<td style="vertical-align: top; width: 113px;">Ev tot<br>
</td>
<td style="vertical-align: top; width: 150px;">
<span style="color: COL_EVIN;">TAG_EVIN</span><br>
</td>
<td style="vertical-align: top; width: 119px;">
<span style="color: COL_EVOUT;">TAG_EVOUT</span><br>
</td>
<td style="vertical-align: top; width: 45px;"><br>
</td>
</tr>
<tr>
<td style="vertical-align: top; width: 113px;">Run<br>
</td>
<td colspan="2" rowspan="1"
style="vertical-align: top; width: 150px;">
<span style="color: COL_RUN;">TAG_RUN</span><br>
</td>
<td style="vertical-align: top; width: 45px;"><br>
</td>
</tr>
<tr>
<td style="vertical-align: top; width: 113px;">LS<br>
</td>
<td colspan="2" rowspan="1"
style="vertical-align: top; width: 150px;">
<span style="color: COL_LS;">TAG_LS</span><br>
</td>
<td style="vertical-align: top; width: 45px;"><br>
</td>
</tr>
<tr>
<td style="vertical-align: top; width: 113px;">PhysDecl<br>
</td>
<td colspan="2" rowspan="1"
style="vertical-align: top; width: 150px;">
<span style="color: COL_PHYSDECL;">TAG_PHYSDECL</span><br>
</td>
<td style="vertical-align: top; width: 45px;"><br>
</td>
</tr>
<tr>
<td style="vertical-align: top; width: 113px;">DCS<br>
</td>
<td colspan="2" rowspan="1"
style="vertical-align: top; width: 150px;">
<span style="color: COL_DCS;">TAG_DCS</span><br>
</td>
<td style="vertical-align: top; width: 45px;"><br>
</td>
</tr>
<tr>
<td style="vertical-align: top; width: 113px;">HLTSel<br>
</td>
<td colspan="2" rowspan="1"
style="vertical-align: top; width: 150px;">
<span style="color: COL_HLTSEL;">TAG_HLTSEL</span><br>
</td>
<td style="vertical-align: top; width: 45px;"><br>
</td>
</tr>
<tr>
<td style="vertical-align: top; width: 113px;">TrigType<br>
</td>
<td colspan="2" rowspan="1"
style="vertical-align: top; width: 150px;">
<span style="color: COL_TRIGTYPE;">TAG_TRIGTYPE</span><br>
</td>
<td style="vertical-align: top; width: 45px;"><br>
</td>
</tr>
<tr>
<td style="vertical-align: top; width: 113px;">L1TT<br>
</td>
<td colspan="2" rowspan="1"
style="vertical-align: top; width: 150px;">
<span style="color: COL_L1TT;">TAG_L1TT</span><br>
</td>
<td style="vertical-align: top; width: 45px;"><br>
</td>
</tr>
</tbody>
</table>
<br>
</body>
</html>
"""

#real main
if __name__=="__main__":
   main()
