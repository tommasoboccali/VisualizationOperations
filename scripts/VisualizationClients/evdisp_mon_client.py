#!/usr/bin/python

from Tkinter import *			# Tk interface
from optparse import OptionParser
import os,string,sys,commands,time,socket,thread,ConfigParser,signal

# global variables
global LAST_REC,INTERVAL,TIMES,label_list,HOSTSERV,TYPE
global SERVER_READY
global GEO
global s_recv

GEO=""
SERVER_READY=False
LAST_REC=''
# graphics
# fixed labels
labels=     ['Network','Ev Rate','Ev tot','Run','LS','PhysDecl','IN','OUT','kB/s','Ev/s','DCS','HLTsel','TrigType','L1TT']
labels_rows=[        1,        2,       3,    4,   5,   6,   0,    0,     1,     2,      7,    8,       9,          10   ]
labels_cols=[        0,        0,       0,    0,   0,   0,   1,    2,     3,     3,      0,    0,       0,           0   ]

LIGHT_LABELS=10

# updating text
win_tag=    ['netin','netout','ratein','rateout','evin','evout','Run','LS','PD','DCS','HLT','TT','L1TT']
win_rows=   [      1,       1,       2,        2,     3,      3,    4,   5,   6,    7,    8,  9,    10 ]
win_row_s=  [      1,       1,       1,        1,     1,      1,    1,   1,   1,    1,    1,  1,     1 ]
win_cols=   [      1,       2,       1,        2,     1,      2,    1,   1,   1,    1,    1,  1,     1 ]
win_col_s=  [      1,       1,       1,        1,     1,      1,    1,   1,   1,    2,    2,  2,     2 ]

WIDTH=      [      6,       6,       6,        6,     6,      6,    6,   6,   6,   30,   30, 10,    30 ]
HEIGHT=     [      1,       1,       1,        1,     1,      1,    1,   1,   1,    4,    7,  1,     1 ] 

LIGHT_WIN=9

values={}
val_status={}
for tags in win_tag:
  values[tags]="-1"
  val_status[tags]="unknown"

# check parameters

# connection parameters
HOSTSERV = ''    # host where thr program runs runs
LOCAL= ''                
PORTSERV = 9005            # send port
#lmtest
#PORTSERV = 9004            # send port
PORTCLIENT = 9006             # receive port
RECEIVED = 0                # flag for tcpserver thread
DATA = ''                   # the answer


def signal_handler(signal, frame):
  global s_recv 
  print 'You pressed Ctrl+C!...closing socket'
  s_recv.close()
  sys.exit(0)

############ TCP COMMUNICATION FUNCTIONS
# function to talk to tcp threshold server
def tcpserver():  
    global RECEIVED,LAST_REC,SERVER_READY,s_recv

    RECEIVED=0
    s_recv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    HOME=socket.gethostname()
    if "pcl3ep01" in HOME:
      HOME='pcl3ep01.cern.ch'
    s_recv.bind((HOME,PORTCLIENT))
      
#    s_recv.bind((socket.gethostname(),PORTCLIENT))
#    s_recv.bind(('pcl3ep01.cern.ch',PORTCLIENT))
   #print socket.gethostname()
    while True:
      s_recv.listen(1)
    #print 'Server starting and waiting for connections on ',PORTCLIENT
      SERVER_READY=True
      (conn, addr)= s_recv.accept()
    #print 'Connected by', socket.gethostbyaddr(addr[0])[0]
      data = conn.recv(1024)
      print 'Received:\n', data
      LAST_REC=data
      RECEIVED=1



def tcpsend(MESSAGE):
   global RECEIVED,SERVER_READY,LAST_REC,HOSTSERV
   
#    SERVER_READY=False
#   thread.start_new_thread(tcpserver,())
   # wait for SERVER_READY
#   WAIT=0
#   while WAIT<5 and not SERVER_READY:
#     WAIT+=1
#     time.sleep(0.2)

#   if not SERVER_READY:
#     print "Server not ready....giving up"
#     LAST_REC=''
#     return

   RECEIVED=0
   s_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   print 'sending to',HOSTSERV,PORTSERV
   try:
     s_send.connect((HOSTSERV, PORTSERV))
   # print 'TCP Sending '+MESSAGE
     s_send.send(MESSAGE)

     WAIT=0
     while RECEIVED==0 and WAIT<50:
       WAIT+=1
       time.sleep(0.1)
       continue

   except socket.error, (val,message):
     print "error in sending: "+message+" proceed...."
     LAST_REC=''

   s_send.close()

   if RECEIVED<=0:
     print "no answer received, proceed with status:",RECEIVED

   print "sending terminated"

def monloop():
    global LAST_REC
    lasttime=1
    lastin=0.
    lastout=0.
    lastevin=0
    lastevout=0
    while True:
        BIN='-1'
        BOUT='-1'
        PD=''
        LL=''
        EV_IN='-1'
        EV_OUT='-1'
        HLT=''
        TT=''
        L1TT=''
        DCS=''
        NETIN='-1'
        NETOUT='-1'
        RATEIN='-1'
        RATEOUT='-1'

        tcpsend("ASK")
        split_ans=string.split(LAST_REC,';')
        for tag in split_ans:
            if tag.find("BIN")!=-1:
                BIN=string.split(tag,":")[1]
            if tag.find("BOUT")!=-1:
                BOUT=string.split(tag,":")[1]
            if tag.find("NETIN")!=-1:
                NETIN=string.split(tag,":")[1]
            if tag.find("NETOUT")!=-1:
                NETOUT=string.split(tag,":")[1]
            if tag.find("RATEIN")!=-1:
                RATEIN=string.split(tag,":")[1]
            if tag.find("RATEOUT")!=-1:
                RATEOUT=string.split(tag,":")[1]
            if tag.find("PD")!=-1:
                PD=string.split(tag,":")[1]
            if tag.find("LL")!=-1:
                LL=string.split(tag,":")[1]
            if tag.find("EVIN")!=-1:
                EV_IN=string.split(tag,":")[1]
            if tag.find("EVOUT")!=-1:
                EV_OUT=string.split(tag,":")[1]
            if tag.find("HLTSEL")!=-1:
                HLT=string.split(tag,":")[1]
            if tag.find("TTSEL")!=-1 and tag.find("L1TTSEL")==-1:
                TT=string.split(tag,":")[1]
            if tag.find("L1TTSEL")!=-1:
                L1TT=string.split(tag,":")[1]
            if tag.find("DCS")!=-1:
                DCS=string.split(tag,":")[1]
            
    
        #print BIN,BOUT,PD,LL,EV_IN,EV_OUT
    
        timedelta=time.time()-lasttime
        lasttime=time.time()
        sin=(float(BIN)-lastin)/(1024*timedelta)
        sout=(float(BOUT)-lastout)/(1024*timedelta)
    
        if EV_IN.isdigit():
            rate_in=(float(EV_IN)-lastevin)/(timedelta)
            lastevin=float(EV_IN)
        else:
            rate_in=0
    
        if EV_OUT.isdigit():
            rate_out=(float(EV_OUT)-lastevout)/(timedelta)
            lastevout=float(EV_OUT)
        else:
            rate_out=0
        print 'NET_IN/OUT: %8.2f/%8.2f kB/s ==== Ev_in/Ev_out: %5.2f/%5.2f Hz === Tot_in/out: %s/%s === PD:%s' % (sin,sout,rate_in,rate_out,EV_IN,EV_OUT,PD)

#        values['netin']=str(sin)
#        if sin==0:
        values['netin']=NETIN
        if float(NETIN)<0.01:
          val_status['netin']='bad'
        else:
          val_status['netin']='good'
          
#        values['netout']=str(sout)
#        if sout==0:
        values['netout']=NETOUT
        if float(NETOUT)<0.01:
          val_status['netout']='bad'
        else:
          val_status['netout']='good'

#        values['ratein']=str(rate_in)
#        if rate_in==0:
        values['ratein']=RATEIN
        if float(RATEIN)<0.01:
          val_status['ratein']='bad'
        else:
          val_status['ratein']='good'

#        values['rateout']=str(rate_out)
#        if rate_out==0:
        values['rateout']=RATEOUT
        if float(RATEOUT)<0.01:
          val_status['rateout']='bad'
        else:
          val_status['rateout']='good'

        values['evin']=EV_IN
        if int(EV_IN)==0:
          val_status['evin']='bad'
        else:
          val_status['evin']='good'

        values['evout']=EV_OUT
        if int(EV_OUT)==0:
          val_status['evout']='bad'
        else:
          val_status['evout']='good'
        
        PD_strip=string.split(PD)
        if len(PD_strip)==3:
          values['Run']=PD_strip[1]
          values['LS']=PD_strip[2]
          values['PD']=PD_strip[0]
        else:
          values['Run']='NA'
          values['LS'] ='NA'
          values['PD'] ='NA'

        if values['Run']=='NA':
          val_status['Run']='unknown'
        else:
          val_status['Run']='good'

        if values['LS']=='NA':
          val_status['LS']='unknown'
        else:
          val_status['LS']='good'

        if values['PD']=='NA':
          val_status['PD']='unknown'
        if values['PD']=='0':
          val_status['PD']='bad'
        if values['PD']=='1':
          val_status['PD']='good'

        DCS=DCS.replace(" ",",")
        values['DCS']=DCS
        if DCS=='':
          val_status['DCS']='unknown'
        elif "None" in DCS:
          val_status['DCS']='bad'
        else:
          val_status['DCS']='good'

        HLT=HLT.replace(" ","")
        HLT=HLT.replace(",","\n")
        values['HLT']=HLT
        if HLT=='':
          val_status['HLT']='unknown'
        elif "None" in HLT:
          val_status['HLT']='bad'
        else:
          val_status['HLT']='good'

        values['TT']=TT
        if TT=='':
          val_status['TT']='unknown'
        elif "None" in TT:
          val_status['TT']='bad'
        else:
          val_status['TT']='good'

        values['L1TT']=L1TT
        if L1TT=='':
          val_status['L1TT']='unknown'
        elif "None" in L1TT:
          val_status['L1TT']='bad'
        else:
          val_status['L1TT']='good'

          

        lastin=float(BIN)
        lastout=float(BOUT)
    
    
        time.sleep(INTERVAL)

###### Graphics monitoring functions

class Example:
  """
  A simple example of how to refresh the GUI automatically every n microseconds
  """

  def __init__(self):
    global INTERVAL,label_list,GEO,TYPE
    # create GUI
    self.root = Tk()
    self.root.title('EvDisp monitoring')
    self.frame = Frame(self.root,name='frame')
    self.frame.grid()
    if (GEO != "None"):
      self.root.geometry(GEO)

    self.label=[]
    self.status=[]

    totlabels=len(labels)
    if TYPE=="light":
      totlabels=LIGHT_LABELS

    for LIST in range(0,totlabels):
      tmplabel = Label(self.frame, text=labels[LIST])
      self.label.append(tmplabel)
      self.label[LIST].grid(column=labels_cols[LIST], row=labels_rows[LIST])

    totwin=len(win_tag)
    if TYPE=="light":
      totwin=LIGHT_WIN
    for LIST in range(0,totwin):
      tmpstatus = Text(self.frame, width=WIDTH[LIST], height=HEIGHT[LIST], bd=1, bg='#0000ff')
      tmpstatus.tag_add('good', 1.0)
      tmpstatus.tag_add('bad', 1.0)
      tmpstatus.tag_add('unknown', 1.0)
      tmpstatus.tag_config('good', background='#00ff00')
      tmpstatus.tag_config('bad', background='#ff0000')
      tmpstatus.tag_config('unknown', background='#0000ff')
      self.status.append(tmpstatus)
      self.status[LIST].grid(column=win_cols[LIST], row=win_rows[LIST],rowspan=win_row_s[LIST], columnspan=win_col_s[LIST])

#    self.quitButton = Button ( self.frame, text='Quit',
#                               command=self.frame.quit )
#    self.quitButton.grid(column=0, row=LIST+1)

    # start counter incrementer at low speed
    self.root.after(INTERVAL*1000,self.incrementer) 


  def incrementer(self):
    global INTERVAL,TYPE
    """
    function to be executed every n milliseconds
    """
    totwin=len(win_tag)
    if TYPE=="light":
      totwin=LIGHT_WIN
    for tag_num in range(0,totwin):
      strval=values[win_tag[tag_num]]
      strstatus=val_status[win_tag[tag_num]]
      self.status[tag_num].insert(1.0,strval.ljust(WIDTH[tag_num]*HEIGHT[tag_num]), strstatus)
    self.root.after(INTERVAL*1000,self.incrementer)



#### MAIN
# here is the main------------------------------------------------------------
#global INTERVAL,SERVER_READY,s_recv,HOSTSERV

parser = OptionParser()
parser.add_option("-t", "--type", dest="type",
                  help="type=textonly,light,full", default="full")
parser.add_option("-i", "--interval", dest="interval",
                  help="poll interval (in sec)", default="5")
parser.add_option("-s", "--server",
                  dest="server", default="vocms89.cern.ch",
                  help="specify a server if different from vocms89.cern.ch")
parser.add_option("-g", "--geometry",
                  dest="geometry", default="None",
                  help="specify a geometry (200x200-0-1200)")

(options, args) = parser.parse_args()

INTERVAL=int(options.interval)
TYPE=options.type
HOSTSERV=options.server
GEO=options.geometry

signal.signal(signal.SIGINT, signal_handler)

SERVER_READY=False
thread.start_new_thread(tcpserver,())

# wait for SERVER_READY
WAIT=0
while WAIT<5 and not SERVER_READY:
  WAIT+=1
  time.sleep(0.2)

if not SERVER_READY:
  print "Server not ready....giving up"
  s_recv.close()
  sys.exit(0)

thread.start_new_thread(monloop,())

if TYPE!="textonly":
  print "Starting graphic interface"
  example = Example()			
  mainloop()

# it should be here only if textonly option is used.
print "imhere"

while True:
  pass
#### END
