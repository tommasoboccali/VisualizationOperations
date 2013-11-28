#!/bin/tcsh
set directory=/afs/cern.ch/cms/CAF/CMSCOMM/COMM_GLOBAL/EventDisplay/RootFileTempStorageArea
set directory_log=/afs/cern.ch/cms/CAF/CMSCOMM/COMM_GLOBAL/EventDisplay/RootFileTempStorageArea/Log
if ($#argv <> 1) then
echo "you must give exactly one parameter, which is the file name you want to cycle"
exit
endif

set file=$1 

while (1)
  echo Pushing file $1
  cp $1 /afs/cern.ch/cms/CAF/CMSCOMM/COMM_GLOBAL/EventDisplay/RootFileTempStorageArea/temp1.root
  sleep 30
  cp $1 /afs/cern.ch/cms/CAF/CMSCOMM/COMM_GLOBAL/EventDisplay/RootFileTempStorageArea/temp2.root
  sleep 30
  touch $directory_log/Skim_fake.log
end

