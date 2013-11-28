//
// How everything works.
//

Overview of the scripts:
1) cmsShow.pl - runs the display and take snap shoots. The arguments are 
   identical to cmsShow. Has to be run from the Fireworks installation 
   directory. In order to take snapshots, make sure that xidle and xrise
   programs are in the PATH otherwise snapshots won't be produced.
2) eventDisplayFeeder.pl - trivial script to send a message to Fireworks
   that a new file is ready
3) monitorFireworks.pl - script is run by a cron job periodically. It 
   checks if other scripts are running and if not, restarts them. 
   It also checks for problems with the machine and communicates errors. 
4) restartFirefoxOnlineSystem - trivial script to (re)start the system.

All scripts are run in the background and controlled by a global flag:
"~/factory_mode". If the file exists all scripts are working normally
otherwise they stop killing all children (this is needed for maintaince).

Port to be used is 9092

Fireworks configuration is defined in ~/default_cmsShow 
The reason for that is to be able to change configuration when it's needed
without changing the scripts. 

If you want to pause the event display feeder staying in the factory mode, 
create a flag file: ~/pauseLiveUpdates
Remove it when you are done.

//
// Transferring images to the web server
//

there is a cron job running on the head node (cmsusr1) that starts
/nfshome0/dmytro/bin/rsync.pl transfer script.

 
=========================================================


/afs/cern.ch/cms/fireworks/beta/cmsShow35
/afs/cern.ch/cms/CAF/CMSCOMM/COMM_GLOBAL/EventDisplay/RootFileTempStorageArea

