#! /bin/bash
#######################################################################################################
#                                                                                                     #
#Script to periodically check if iguana is running and establish its current status to determine      #
#if it must be restarted.                                                                             #
#                                                                                                     #
#based on Hyunkwan's alivecheck_dqmPostProcessing.sh                                                  #
#                                                                                                     #
# Luis Ignacio Lopera lilopera@cern.ch                                                                #
#                                                                                                     #
#######################################################################################################

#ispy --online srv-c2d05-15.cms:9000 /home/vis/iSpy/cms-detector.ig
xset -dpms

#Globals
IMAGE_DIR="/home/vis/EventDisplay/images"
DETECTOR_GEOMETRY="/home/vis/iSpy/cms-detector.ig"
CUTS_ISS="/home/vis/iSpy/cuts.iss"
VIEWS_IML="/home/vis/iSpy/online-views.iml"
WORKING_DIR="/home/vis/iglogs"

#Client Names:
CLIENT0="P5"
CLIENT1="CMSCC"

#Producer Connection strings (--online ):
SRV_PORT_C0="vocms89:9001"
SRV_PORT_C1="vocms89:9000"

#Log files
igLOG_CLIENT0=$WORKING_DIR"/iSpylog_"$CLIENT0"_"`date +%Y%m%d_%H%M`"_"$HOSTNAME				#Output grabber
igLOG_CLIENT1=$WORKING_DIR"/iSpylog_"$CLIENT1"_"`date +%Y%m%d_%H%M`"_"$HOSTNAME				#Output grabber

igABORT_BASE_LOG_FILE="/home/vis/iSpy/iglogs/igAbort"		#Base file name for abort handeling
NUM_LINES=40						                #Number of lines to log

#YourEmail=liloperavim@cern.ch
#cronjob entry: */10 * * * * /home/vis/iSpy/iglogs/livelyiSpy.sh  >> /home/vis/iSpy/iglogs/ispyLiveCheck 2>&1
KDMPID=$([ $(stat -c %U /proc/$(/sbin/pidof -x  /usr/bin/startkde)) == vis ] && /sbin/pidof -x  /usr/bin/startkde)
GDMPID=$([ $(stat -c %U /proc/$(/sbin/pidof  gnome-session)) == vis ] && /sbin/pidof gnome-session)
REASON="Unknown"

if [[ -z $KDMPID && -z $GDMPID ]]
then
	exit
fi
if [ -z $KDMPID ] 
then
	eval `tr '\0' '\n' < /proc/$GDMPID/environ | grep XAUTHORITY` 	
else
	eval `tr '\0' '\n' < /proc/$KDMPID/environ | grep XAUTHORITY` 	
fi

export XAUTHORITY

if [[ $1 =~ \-\-restart ]]
    then
      killall -9 ispy
      REASON="Forced Restart"
    fi

timestamp=$(date +%Y%m%d)
if [[ $HOSTNAME =~ scx5scr36* || $HOSTNAME =~ SCX5SCR36* ]]
then
  names=$CLIENT0  
  dirs=$IMAGE_DIR/$timestamp/$CLIENT0
  logfiles=$igLOG_CLIENT0
  srvports=$SRV_PORT_C0
  numClients=1
  export DISPLAY=:0.0
else
  names=$CLIENT1
  dirs=$IMAGE_DIR/$timestamp/$CLIENT1
  logfiles=$igLOG_CLIENT1
  srvports=$SRV_PORT_C1
  numClients=1
  export DISPLAY=:0.0
fi
i=0
while [[ $i -lt $numClients ]]
do
  
  pid=-1
  RUN_STAT=0
  if [ -e $WORKING_DIR/pid${names[$i]} ]
  then
    pid=$(cat $WORKING_DIR/pid${names[$i]})
    RUN_STAT=$([[ $pid != "" ]] && echo $(ps -eo pid | grep -oP "\b${pid}\b" | grep -v grep | wc -l))
  fi  
  if [[ $RUN_STAT -eq 0 ]]   
  then
    if [ ! -d ${dirs[$i]} ]
    then
      mkdir -p ${dirs[$i]}
    fi
    export ISPY_AUTO_PRINT_PATH=${dirs[$i]} 
    export ISPY_AUTO_PRINT=1 
echo     /home/vis/iSpy/ispy  ${CUTS_ISS} ${VIEWS_IML} --online ${srvports[$i]} ${DETECTOR_GEOMETRY}
    /home/vis/iSpy/ispy  ${CUTS_ISS} ${VIEWS_IML} --online ${srvports[$i]} ${DETECTOR_GEOMETRY}  1>${logfiles[$i]} 2>&1 &
    echo $! > $WORKING_DIR/pid${names[$i]}
    echo `date +"%Y/%m/%d %H:%M:%S"` WARNING: iSpy Online ${names[$i]} was not Running and has been restarted, reason: $REASON
    echo `date +"%Y/%m/%d %H:%M:%S"` INFO:    Creating logfile ${logfiles[$i]}
  else
    echo `date +"%Y/%m/%d %H:%M:%S"` INFO: iSpy Online ${names[$i]} Running
  fi
  i=$(( i + 1 ))
done
