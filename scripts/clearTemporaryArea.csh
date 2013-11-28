#!/bin/tcsh 

#
# so: try and have files lasting at least $retention_time; 
#
#
# dquota is the quota of the area
# minfree must be the minimum free area to complete current operations
#

# if disk used more than $maxdisk, delete the oldest ones respecting the previous requirement
# if disk used more than $maxdisk, delete the oldest ones without respecting the previous requirement, but then send a WARNING
if ($#argv != 1) then
        echo "Usage: $0 <directory>"
        exit 1
endif

set verb=1

set AREA=$1

#
# in hours
#

set retention_time=10
set retention_time2=4

#
# disk quota (in kB)
#

# this is 5 GB
set dquota=10000000

#
# minfree (in kB)
#

# this is 1 GB
set minfree=6000000

@ maxdisk= $dquota - $minfree

if ($verb) then
    echo Setting maxdisk to $maxdisk
endif
#
# get disk used
#
cd $AREA
fs flush .
fs flush ./Log
set used=`du -s |awk '{print $1}'`

if ($verb) then
    echo Used disk is $used
endif


if ($used < $maxdisk) then
#
# nothing to do
#
if ($verb) then
    echo Exit with code 0
endif

exit 0
endif

/usr/sbin/tmpwatch --verbose -d --atime $retention_time .
# first test - see if you can clean applying retention time
if ($used > $maxdisk) then
if ($verb) then
    echo Running tmpwatch
endif
 /usr/sbin/tmpwatch --verbose -d --atime $retention_time . 
endif
#
# now look whether situation is good
#
set newused=`du -s |awk '{print $1}'`

if ($verb) then
    echo Now used is $newused
endif
#force log celaning
/usr/sbin/tmpwatch --verbose -d --atime 2 ${AREA}/Log 
if ($newused < $maxdisk) then
#
# I am happy, I bail out
# exit 2 = i had to delete, but just stuff I could delete
exit 2
endif
#
# try with retentiontime2 before going on
#
 /usr/sbin/tmpwatch --verbose -d --atime $retention_time2 .
set newused=`du -s |awk '{print $1}'`
if ($newused < $maxdisk) then
#
# I am happy, I bail out
# exit 2 = i had to delete, but just stuff I could delete
exit 2
endif


#
# else, delete files in order of age, one by one
#
set oldfile="aaa"
while ($newused > $maxdisk)
 #
 # find the oldest file
 set file=`ls -t1 *root|tail -1`
 if ($file =="") then
    echo Not enough files to kill, I bail out
    exit 4 
 endif
 if ($file ==$oldfile) then
    echo something fishy, probably a file cannot be deleted, I bail out
    exit 5
 endif
 if ($verb) then
    echo Deleting $file  
endif
 rm -f $file
 set $oldfile=$file
 #calculate new disk free
 set newused=`du -s |awk '{print $1}'`
if ($verb) then
    echo Now free is $newused 
endif
#
end

#exit three means I had to delete stuff not expired
exit 3

#
