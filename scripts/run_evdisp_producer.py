#!/usr/bin/env python
import os,string,sys,commands,time,subprocess,signal,ConfigParser,thread
import re


global MODCFG,DRYRUN,RAW2DIGISEQ,RECOSEQ,INPUTCFG,KILLING,AREA,TYPE

CONFIGFILE="run_evdisp_producer.cfg"

CONFIG = ConfigParser.ConfigParser()
CONFIG.read(CONFIGFILE)

HOWMANY=CONFIG.get('Common','Producers')


MODCFG=""
RECOSEQ=""
RAW2DIGISEQ=""
DRYRUN=False
T0MONSERVER="cmsweb.cern.ch"

PROC=[]
procevd=0
proclastfile=0
procphdecl=0

def main():
    # main starts here
    global MODCFG,DRYRUN,RAW2DIGISEQ,RECOSEQ,INPUTCFG,GLOBALTAG,SCENARIO,SCENARIOFROMDAS,T0MONSERVER
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT,handler)
    if len(sys.argv)!=1:
        if sys.argv[1]!="dryrun":
            print "Usage: "+sys.argv[0]+" [dryrun]"
            sys.exit(0)
        else:
            DRYRUN=True


#    print MODCFG
#    sys.exit(1)

    SCENARIO=""
    SCENARIOFROMDAS=""

    for instance in range(0,int(HOWMANY)):
        thread.start_new_thread(runproducer,(instance,))
        # stagger them a bit...
        time.sleep(1)

    # start other servers
    if not DRYRUN:
        thread.start_new_thread(runevdserver,())
        thread.start_new_thread(runlastfile,())
        thread.start_new_thread(runphdecl,())
        thread.start_new_thread(killperiodically,())
        thread.start_new_thread(killingperiodicallycmsRun,())
        thread.start_new_thread(killincmsRunOnScenarioChange,())
 #          time.sleep(2) 
    time.sleep(2) 
        
    while True:
        # just wait forever....
        time.sleep(100000)



def getScenario():
    global T0MONSERVER

    print "DDDD "+T0MONSERVER

    while (1):
        bad = 1;
        while (bad == 1):
            dasinfo2=commands.getoutput("wget  --no-check-certificate "+T0MONSERVER+"    -o /dev/null -O /dev/stdout")
            if (dasinfo2 ==""):
                print "retrying DAS..."
                time.sleep(117)
            else:
                bad=0
            #dasinfo2 = "[{'expversion': 'CMSSW_5_2_7_hltpatch1', 'scenario': 'pp', 'stream': 'HLTMON', 'run_id': 209520, 'proc_version': 4, 'global_tag': 'GR_E_V29::All'}, {'expversion': 'CMSSW_5_3_6', 'scenario': 'cosmics', 'stream': 'ExpressCosmics', 'run_id': 209520, 'proc_version': 4, 'global_tag': 'GR_E_V31::All'}]"
	    #dasinfo2="[{'expversion': 'CMSSW_5_3_8_HI', 'splitinprocessing': 1, 'config_url': None, 'run_id': 210022, 'scenario': 'pp', 'proc_version': 'v1', 'global_tag': 'GR_E_V33::All', 'stream': 'Express', 'alcamerge_config_url': None}]"
            dasinfo2=dasinfo2.replace("[","")
            dasinfo2=dasinfo2.replace("]","")
            exec("daslist2="+dasinfo2)
            #
            # loop over it
            print " TYPE IS ", type(daslist2).__name__
            if (type(daslist2).__name__ == 'dict'):
		if (re.match('Express',daslist2['stream'])):
                    return (daslist2['scenario'],daslist2['global_tag'])
            elif  (type(daslist2).__name__ == 'tuple'):
                for d in (daslist2):
                 if (re.match('Express',d['stream'])):
                    return (d['scenario'],d['global_tag'])
            
            print "Error - could not understand from DAS the operating mode"
            time.sleep (117)
    



def handler (signum,frame):
    global KILLING
    
    KILLING=True
    for instance in range(0,int(HOWMANY)):
        if not DRYRUN:
            try:
                print "Killing run producer instance: "+str(instance)
                PROC[instance].kill()
            except:
                print "Problem in killing instance:"+str(instance)
                
    try:
        procevd.terminate()
        time.sleep(1)
    except:
        print "Problem in killing evdisp_mon_server"
    try:
        proclastfile.kill()
    except:
        print "Problem in killing lastfile producer"

    try:
        procphdecl.kill()
    except:
        print "Problem in killing physdecl producer"
    sys.exit()



def killincmsRunOnScenarioChange():
    global SCENARIO,SCENARIOFROMDAS,T0MONSERVER
    while True:
	time.sleep(117)
        if (SCENARIOFROMDAS!=""):
# get new scenario
       	 (NEWSCENARIO,NEWGT) = getScenario()
         print " FROM DAS "+SCENARIOFROMDAS+" SCENARIO IS "+SCENARIO+" NEW IS "+NEWSCENARIO
         if (NEWSCENARIO != SCENARIO and SCENARIO!=""):
             print "==============Killing cmsRun instances since scenarion changed to "+NEWSCENARIO
             os.system("killall -9 cmsRun")	


def killingperiodicallycmsRun():
    while True:
        time.sleep(3000)
        print "==============Killing cmsRun instances"
        os.system("killall -9 cmsRun")
#        for instance in range(0,int(HOWMANY)):
#            try:
#                print "Killing run producer instance: "+str(instance)
#                PROC[instance].kill()
#            except:
#                print "Problem in killing instance:"+str(instance)
#                os.system("killall -9 cmsRun")


def killperiodically():
    global procevd,proclastfile,pocphdecl
    while True:
        time.sleep(600)
        try:
            print "Killing "+str(procevd.pid)
            procevd.terminate()
        except:
            print "Problem in killing evdmon"
        try:
            print "Killing "+str(proclastfile.pid)
            os.system("killall check_lastFile")
        #proclastfile.kill()
        except:
            print "Problem in killing check_lastFile"
        try:
            print "Killing "+str(procphdecl.pid)
            os.system("killall check_physdecl_server")
        #procphdecl.kill()
        except:
            print "Problem in killing check_physdec"

def runevdserver():
    global procevd
#
# start the first instance, killing all of the existing before
#    
    EXISTING_PID=commands.getoutput("ps -ef |grep evdisp_mon_server.py |grep -v grep |awk '{print $2}'")
    if EXISTING_PID != "" :
        print "killing running evdisp_mon_server: "+EXISTING_PID
        os.system("kill -9 "+EXISTING_PID)
        time.sleep(1)
        
    while not KILLING:
        procevd = subprocess.Popen("./evdisp_mon_server.py "+AREA+"/Log", stdin=None, stdout=None, stderr=subprocess.STDOUT, shell=True) 
        print "Starting EVDMon "+str(procevd.pid)
        while procevd.poll()==None:
            time.sleep(10)
            #os.system("date");
            #print"in the wait loop for runevdserver"
        


def runlastfile():
    global proclastfile,AREA
    os.system("killall check_lastFile")

    while not KILLING:
        proclastfile = subprocess.Popen("./check_lastFile "+AREA, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        print "Starting Check_last_file "+str(proclastfile.pid)
        while proclastfile.poll()==None:
            time.sleep(10)
            #print"in the wait loop for runlastfile"
 

def runphdecl():
    global procphdecl
    os.system("killall check_physdecl_server")

    while not KILLING:
        procphdecl = subprocess.Popen("./check_physdecl_server "+AREA, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        print "Starting Check_phys_decl "+str(procphdecl.pid)
        while procphdecl.poll()==None:
            time.sleep(10)
            #print"in the wait loop for runphdecl"

        



def runproducer(instance):
    global SCENARIO,DRYRUN,RAW2DIGISEQ,RECOSEQ,KILLING,AREA,INPUTCFG,GLOBALTAG,SCENARIOFROMDAS,STREAM,TRIGGERTYPE,L1TTSEL,HLTSEL,SELININPUT,MODCFG,CONFIGFILE,TYPE,T0MONSERVER

    KILLING=False
    
    while not KILLING:
#
# clean variables
#


        CONFIG = ConfigParser.ConfigParser()
        CONFIG.read(CONFIGFILE)
        
        HOWMANY=CONFIG.get('Common','Producers')
        AREA=CONFIG.get('Common','Out_Area')
        NUMEVENTS=CONFIG.get('Common','Events')
        TYPE=CONFIG.get('Common','Type')

	T0MONSERVER=CONFIG.get('Common','T0MonServer')
        
        if TYPE=='pr':
            NUMEVENTS='20'

        HLTSEL="None"
        TRIGGERTYPE="None"
        L1TTSEL="None"
        INPUTCFG="None"
        GLOBALTAG="None"
        STREAM="None"
        SCENARIO="None"
        SELECTININPUT=False
        FILEPR='None'
        
        FILEPR=CONFIG.get('Common','InputPRFile')

# The following are optionals and in case absent, no filtering is applied
        SELININP="False"
        CFGLIST=CONFIG.items('Common')
        for item in CFGLIST:
            if item[0]=="hltsel":
                HLTSEL=item[1]
            if item[0]=="triggertype":
                TRIGGERTYPE=item[1]
            if item[0]=="l1_techtrig":
                L1TTSEL=item[1]
            if item[0]=="recocfg":
                INPUTCFG=item[1]
            if item[0]=="globaltag":
                GLOBALTAG=item[1]
            if item[0]=="stream":
                STREAM=item[1]
            if item[0]=="scenario":
		SCENARIO=item[1]
            if item[0]=="selectininput":
                SELININPUT=item[1]

        if SELININPUT=="True":
            SELECTININPUT=True
                

        AREALOG=AREA+"/Log"

        MODCFG=""
        RECOSEQ=""
        RAW2DIGISEQ=""
        DRYRUN=False

        #
        # clean area
        #
        if instance==0:
            PREFIX=AREALOG+"/SkimSM"
            if not DRYRUN:
                os.system("./clearTemporaryArea.csh "+AREA)

        elif instance==1:
            PREFIX=AREALOG+"/SkimSM_second"
        else:
            PREFIX=AREALOG+"/SkimSM_"+str(instance+1)

        print "Starting producer instance n."+str(instance)
        DATE=str(int(time.time()))
        
        print "Suffix:"+DATE

#
# move here the generation of the config
#
        if GLOBALTAG=="None" or STREAM=="None":
# i interject here
# i need to wait for DAS in case it is down!!!!
           (SCENDAS,GTDAS) = getScenario()

        GTFROMDAS=""
        if GLOBALTAG=="None":
            GLOBALTAG=GTDAS
            GTFROMDAS="(From DAS)="

        SCENARIOFROMDAS=""
        if SCENARIO=="None":
            SCENARIO=SCENDAS
            SCENARIOFROMDAS="(From DAS)="

        CFGFROMDAS=""
        if INPUTCFG=="None":
            INPUTCFG="RunExpressProcessing.py --scenario="+SCENARIO+" --lfn=/store/test --global-tag="+GLOBALTAG
            CFGFROMDAS="(From DAS)="
        

	STREAMFROMDAS="" 
        if STREAM=="None":
	   if SCENARIO=="pp":
	       STREAM="hltOutputExpress"
	   if SCENARIO=="HeavyIons": # dp changed for HI
	       STREAM="hltOutputHIExpress"
	   if SCENARIO=="cosmics":
	       STREAM="hltOutputExpressCosmics"
           STREAMFROMDAS="(From DAS)="

        if STREAM=="None":
            print" Could not set a valid STREAM "
            exit()
	  
        SOURCE=""

        if TYPE=="tunnel" :
            SOURCE="cms.string('http://localhost:22100/urn:xdaq-application:lid=30')"
            SELECTHLT= "cms.untracked.string('"+STREAM+"')"
        elif TYPE=="revproxy":
            SOURCE="cms.string('http://cmsdaq0.cern.ch/event-display/urn:xdaq-application:lid=30')"
            SELECTHLT= "cms.untracked.string('"+STREAM+"')"
        elif TYPE=="playback":
            SOURCE="cms.string('http://localhost:50082/urn:xdaq-application:lid=29')"
            SELECTHLT= "cms.untracked.string('"+STREAM+"')"
        elif TYPE=="pr":
            SELECTHLT= "cms.untracked.string('*')"
        else:
            print "wrong type value."
            sys.exit(1)

# first report what is there
        print ' '
        print '########################################################'
        print 'Reading configuration file from ',CONFIGFILE
        print '########################################################'
        print ' '
        print 'Parameters:'
        print '--------------------------------------------------------'
        print 'Number of producers :',HOWMANY
        print 'Original reco cfg   :',CFGFROMDAS,INPUTCFG
        print 'Output area         :',AREA
        print 'Events in single job:',NUMEVENTS
        print 'Type of connection  :',TYPE,"( ",SOURCE," )"
        print 'GlobalTag           :',GTFROMDAS,GLOBALTAG
        print 'Scenario            :',SCENARIOFROMDAS,SCENARIO 
        print 'T0MonServer         :',T0MONSERVER
        print 'HLT selection       :',HLTSEL
        print 'Trigger Type select.:',TRIGGERTYPE
        print 'L1 TechTrig  select.:',L1TTSEL
        print 'Stream              :',STREAMFROMDAS,STREAM
        print '--------------------------------------------------------'
        print ' '



 
        if "RunExpressProcessing.py" in INPUTCFG:
            print "Running Script to get the Config:"
            print "Command: "+INPUTCFG
            os.system("python ../../../Configuration/DataProcessing/test/"+INPUTCFG)
            INPUTCFG="RunExpressProcessingCfg.py"


# then define string
        definecfg()

# find the rawtodigi and the reconstruction sequences
        for line in MODCFG.split("\n"):
            if "raw2digi_step" in line and "cms.Path" in line:
                RAW2DIGISEQ=line.split("cms.Path(")[1]
                RAW2DIGISEQ=RAW2DIGISEQ.split(")")[0]
            if "reconstruction_step" in line and "cms.Path" in line:
                RECOSEQ=line.split("cms.Path(")[1]
                RECOSEQ=RECOSEQ.split(")")[0]


        MODCFG=MODCFG.replace("MYFILEINPUT",FILEPR)

# replace common values
        MODCFG=MODCFG.replace("TAG_NUMEVENTS",NUMEVENTS)
        MODCFG=MODCFG.replace("TAG_SOURCE",SOURCE)
        MODCFG=MODCFG.replace("TAG_SELECTHLT",SELECTHLT)
        MODCFG=MODCFG.replace("TAG_EVDISPSM_DIR",AREA)
        MODCFG=MODCFG.replace("TAG_GLOBALTAG",GLOBALTAG)
        if HLTSEL=="None":
            MODCFG=MODCFG.replace("TAG_HLTSEL","\'None\'")
        else:
            MODCFG=MODCFG.replace("TAG_HLTSEL",HLTSEL)
            
        if HLTSEL=="None" or SELECTININPUT==False:
            MODCFG=MODCFG.replace("TAG_2HLTSEL","\'*\'")
        else:
            MODCFG=MODCFG.replace("TAG_2HLTSEL",HLTSEL)


        if TRIGGERTYPE=="None":
            MODCFG=MODCFG.replace("TAG_TRIGGERTYPE","999")
        else:
            MODCFG=MODCFG.replace("TAG_TRIGGERTYPE",TRIGGERTYPE)
            
        if L1TTSEL=="None":
            MODCFG=MODCFG.replace("TAG_L1TTSEL","\'None\'")
        else:
            MODCFG=MODCFG.replace("TAG_L1TTSEL",L1TTSEL)

        if SCENARIO=="HeavyIons":
	   MODCFG=MODCFG.replace("TAGEVENTCONTENT","EventContentHeavyIons")
 	elif SCENARIO=="cosmics":
	   MODCFG=MODCFG.replace("TAGEVENTCONTENT","EventContentCosmics")	
        else:
           MODCFG=MODCFG.replace("TAGEVENTCONTENT","EventContent")

#
# end of changes
#


        FILENAME=PREFIX+"_"+DATE+"_cfg.py"
        FILELOG=PREFIX+"_"+DATE+".log"
    # read mod file
        THISCFG=MODCFG
        THISCFG=THISCFG.replace("TAG_SUFFIX",DATE)
        THISCFG=THISCFG.replace("TAG_PORT",str(9000+instance))

        if instance==0:
            THISCFG+="""
process.out_step=cms.EndPath(process.FEVT)
"""

        FULLPATH="process.fullpath=cms.Path(process.hltinspect+"    
        if TRIGGERTYPE!="None": 
            FULLPATH+="process.hltTriggerTypeFilter+"
        if HLTSEL!="None": 
            FULLPATH+="process.hltHighLevel+"
 
        FULLPATH+=RAW2DIGISEQ+"+"
        if L1TTSEL!="None":
           FULLPATH+="process.hltLevel1GTSeed+"

	FULLPATH+=RECOSEQ+"+process.l1GtTriggerMenuLite+process.beamsplash+process.physdecl+process.dcsstatus)"
          
        THISCFG+=FULLPATH+"\n"
        if instance==0:
#            THISCFG+="process.schedule=cms.Schedule(process.fullpath,process.ispypath,process.out_step)"
            THISCFG+="process.schedule=cms.Schedule(process.fullpath,process.out_step)"
        else:
#            THISCFG+="process.schedule=cms.Schedule(process.fullpath,process.ispypath)"
            THISCFG+="process.schedule=cms.Schedule(process.fullpath)"

#        SCHEDULE+="process.raw2digi_step,process.reconstruction_step,process.skimming,process.Monitoring,process.ispy)"
#        SCHEDULE=""
#        if L1TTSEL!="None": 
#            SCHEDULE+="process.techtrigger,"
#        if TRIGGERTYPE!="None": 
#            SCHEDULE+="process.triggertype,"
#        if HLTSEL!="None": 
#            SCHEDULE+="process.hltfilter,"
#            
#        SCHEDULE+="process.raw2digi_step,process.reconstruction_step,process.skimming,process.Monitoring,process.ispy"
#        if instance==0:
#            THISCFG+="process.schedule=cms.Schedule("+SCHEDULE+",process.out_step)"
#        else:
#            THISCFG+="process.schedule=cms.Schedule("+SCHEDULE+")"

        # write a selection summary at the end of file
        THISCFG+="\n"
        THISCFG+="################################################"
        THISCFG+="# Selection summary\n"
        THISCFG+="# HLTSEL= "+HLTSEL+"\n"
        THISCFG+="# TRIGGERTYPE= "+TRIGGERTYPE+"\n"
        THISCFG+="# L1TTSEL= "+L1TTSEL+"\n"

        # in order to have it on the log file for later parsing
        # replace double quotes in case.....(otherwise print is confused)
        TMP=HLTSEL.replace("\"","'")
        THISCFG+="print \"HLT_selection: "+TMP+"\"\n"
        TMP=TRIGGERTYPE.replace("\"","'")
        if TRIGGERTYPE=="0" : TMP="random"
        if TRIGGERTYPE=="1" : TMP="physics"
        if TRIGGERTYPE=="2" : TMP="calibration"
        if TRIGGERTYPE=="3" : TMP="technical"
        THISCFG+="print \"Triggertype_selection: "+TMP+"\"\n" 
        TMP=L1TTSEL.replace("\"","'")
        THISCFG+="print \"TechTrigger_selection: "+L1TTSEL+"\"\n" 


        print "OPENING"+FILENAME

        newfile=open(FILENAME,"w")
        newfile.write(THISCFG)
        newfile.close()
                 
        print "Created: "+FILENAME
        print "Running cmsRun now and logging in "+FILELOG
        if DRYRUN:
            return

        print "START"

        proc = subprocess.Popen("cmsRun "+FILENAME+" 2>&1 | tee "+FILELOG+" | grep --line-buffered Clos", stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

        if len(PROC)<instance+1:
            PROC.append(proc)
        else:
            PROC[instance]=proc
            
        print "Instance: "+str(instance)+" procid= "+str(proc.pid)
        while proc.poll()==None:
#            time.sleep(1)
            print "***** PRODUCER:"+str(instance)+" *******   "+proc.stdout.readline(),
        print " I have to sleep for 20 seconds; thanks for your patience..."
        time.sleep(20)
      

def definecfg():
    global MODCFG,INPUTCFG,TYPE
    modfile=open(INPUTCFG,"r")
    MODCFG=modfile.read()
    modfile.close()

#
# first prepare the sources for the various cases
#
    SOURCEHTTP = """
process.source = cms.Source("EventStreamHttpReader",
   sourceURL = TAG_SOURCE,
   consumerName = cms.untracked.string('Event Display'),
   consumerPriority = cms.untracked.string('normal'),
   max_event_size = cms.int32(7000000),
   SelectHLTOutput = TAG_SELECTHLT,
   max_queue_depth = cms.int32(5),
   maxEventRequestRate = cms.untracked.double(100.0),
   SelectEvents = cms.untracked.PSet(
       SelectEvents = cms.vstring(TAG_2HLTSEL)
   ),
   headerRetryInterval = cms.untracked.int32(3)
)

"""

    SOURCEFILE="""
process.source = cms.Source("PoolSource",
    fileNames = cms.untracked.vstring("MYFILEINPUT")
    )
"""


#replace the previuos schedule
    # first individuate cms.Schedule and merge split lines
    TMP1=MODCFG.split("cms.Schedule(")
    TMP2=TMP1[1].split(")")
    INTERNAL=TMP2[0]
    NEWINTERNAL=INTERNAL.replace("\n","")
    MODCFG=MODCFG.replace(INTERNAL,NEWINTERNAL)
    
    COMMENT="""
#REMOVED BY EVDISP PRODDUCER
#process.schedule"""
    MODCFG=MODCFG.replace("process.schedule",COMMENT)

    MODCFG+="""

######### FROM HERE ADDED BY EVDISP PRODUCER #########################
####### GENERAL SECTION #############################################

process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(TAG_NUMEVENTS)
)
process.options = cms.untracked.PSet(
    Rethrow = cms.untracked.vstring('ProductNotFound'),
    wantSummary = cms.untracked.bool(True)
)

process.load('Configuration.EventContent.TAGEVENTCONTENT_cff')

######### SOURCE Section #############################

INSERTHEREMYSOURCE


######### GLOBALTAG Section #############################
process.GlobalTag.globaltag = 'TAG_GLOBALTAG'


######### FILTERING Section #############################
# this is for filtering on HLT path
process.hltHighLevel = cms.EDFilter("HLTHighLevel",
     TriggerResultsTag = cms.InputTag("TriggerResults","","HLT"),
     HLTPaths = cms.vstring(           # provide list of HLT paths (or patterns) you want
     TAG_HLTSEL
                                    ),
     eventSetupPathsKey = cms.string(''), # not empty => use read paths from AlCaRecoTriggerBitsRcd via this key
     andOr = cms.bool(True),             # how to deal with multiple triggers: True (OR) accept if ANY is true, False (AND) accept if ALL are true
     throw = cms.bool(False)    # throw exception on unknown path names
 )

process.hltfilter=cms.Path(process.hltHighLevel)

# this is for filtering based on reco variables
process.beamsplash = cms.EDFilter("BeamSplash",
    energycuttot = cms.untracked.double(1000.0),
    energycutecal = cms.untracked.double(700.0),
    energycuthcal = cms.untracked.double(700.0),
    ebrechitcollection =   cms.InputTag("ecalRecHit","EcalRecHitsEB"),
    eerechitcollection =   cms.InputTag("ecalRecHit","EcalRecHitsEE"),
    hbherechitcollection =   cms.InputTag("hbhereco"),
    applyfilter = cms.untracked.bool(False)                            
)

process.skimming=cms.Path(process.beamsplash)

# this is for filtering on trigger type

process.load("HLTrigger.special.HLTTriggerTypeFilter_cfi")
# 0=random, 1=physics, 2=calibration, 3=technical
process.hltTriggerTypeFilter.SelectedTriggerType = TAG_TRIGGERTYPE

process.triggertype=cms.Path(process.hltTriggerTypeFilter)

# this is for filtering on L1 technical trigger bit
process.load('L1TriggerConfig.L1GtConfigProducers.L1GtTriggerMaskTechTrigConfig_cff')
process.load('HLTrigger/HLTfilters/hltLevel1GTSeed_cfi')
process.hltLevel1GTSeed.L1TechTriggerSeeding = cms.bool(True)
process.hltLevel1GTSeed.L1SeedsLogicalExpression = cms.string(TAG_L1TTSEL)
process.techtrigger=cms.Path(process.hltLevel1GTSeed)

#this is for filtering/tagging PhysDecl bit
process.physdecl = cms.EDFilter("PhysDecl",
     applyfilter = cms.untracked.bool(False),
     debugOn = cms.untracked.bool(True),
# the following needs V00-01-19 of DPGAnalysis/Skims!!!
     HLTriggerResults = cms.InputTag("TriggerResults","","HLT")

    )
process.Monitoring=cms.Path(process.physdecl)
# add hlt inspect option
process.hltinspect = cms.EDAnalyzer("HLTInspect",
 HLTriggerResults = cms.InputTag("TriggerResults","","HLT")
)

process.dcsstatus = cms.EDFilter("DetStatus",
           DetectorType= cms.vstring(''),
           ApplyFilter = cms.bool(False), 
           DebugOn     = cms.untracked.bool(True), 
           AndOr       = cms.bool(True) # True=And, Flase=Or              
)
#
# from vincenzo
#
process.GlobalTag.RefreshEachRun=cms.untracked.bool(True)
#
# from suchandra
#
#--------------------------------------------
## Patch to avoid using Run Info information in reconstruction
#
process.siStripQualityESProducer.ListOfRecordToMerge = cms.VPSet(
  cms.PSet( record = cms.string("SiStripDetVOffRcd"),    tag    = cms.string("") ),
  cms.PSet( record = cms.string("SiStripDetCablingRcd"), tag    = cms.string("") ),
#  cms.PSet( record = cms.string("RunInfoRcd"),           tag    = cms.string("") ),
  cms.PSet( record = cms.string("SiStripBadChannelRcd"), tag    = cms.string("") ),
  cms.PSet( record = cms.string("SiStripBadFiberRcd"),   tag    = cms.string("") ),
  cms.PSet( record = cms.string("SiStripBadModuleRcd"),  tag    = cms.string("") )
  )
#-------------------------------------------


process.RECOEventContent.outputCommands.append("keep *_l1GtTriggerMenuLite_*_*")
process.l1GtTriggerMenuLite = cms.EDProducer("L1GtTriggerMenuLiteProducer")

process.FEVT = cms.OutputModule("TimeoutPoolOutputModule",
    process.RECOEventContent,
    maxSize = cms.untracked.int32(3000),
    fileName = cms.untracked.string('TAG_EVDISPSM_DIR/EVDISPSM_TAG_SUFFIX.root'),
#    outputCommands = cms.untracked.vstring('keep *','drop *_MEtoEDMConverter_*_*'),
    dataset = cms.untracked.PSet(
    	      dataTier = cms.untracked.string('RAW-RECO'),
    	      filterName = cms.untracked.string('EVDISP')),
                                SelectEvents = cms.untracked.PSet(
        SelectEvents = cms.vstring('fullpath')
    )
)
"""

#
# impose the source
#
    if TYPE=="pr":
        MODCFG=MODCFG.replace("INSERTHEREMYSOURCE",SOURCEFILE)
    else:
        MODCFG=MODCFG.replace("INSERTHEREMYSOURCE",SOURCEHTTP)


    
if __name__=="__main__":
   main()
