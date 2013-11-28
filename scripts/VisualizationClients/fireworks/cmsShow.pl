#!/bin/env perl
#
# Created by dmytro.kovalskyi@cern.ch
#
use warnings;
use strict;
use POSIX qw( WNOHANG sys_wait_h );
use Fcntl;
use Proc::Killfam;

die "You have to provide a full set of parameters to start cmsShow.\n".
    "At least it should contain a file name to show.\n" unless @ARGV>0;
# tot is the total numer of images put - so that I can skip
my $tot=0;
my $window_name = "cmsShow: $ARGV[$#ARGV]";
print "\nStarting cmsShow.pl with the following paramteres:\n";
print join(" ",@ARGV), "\n";
my $outputDir = "$ENV{HOME}/screenshots/";
my $outputtmp = "$ENV{HOME}/screenshots/tmp.png";
my $logFile = "$ENV{HOME}/fireworks/log/cmsShow.log";
my $timeoutToEstablishControl = 100;  # seconds
my $timeoutToDetectUserActivity = 60; # seconds

my $report = "$ENV{HOME}/status/screenshot.error";

my $take_snapshots = 1;
$take_snapshots = 0 if ( `which xidle 2>/dev/null` !~ /\S/ );
$take_snapshots = 0 if ( `which xraise 2>/dev/null` !~ /\S/ );
print("Warning: either xidle or xraise are not available. Now screenshot will be produced\n");
my $message = "";
umask 0;

sub quit{
    my ($message, $child_id) = @_;
    if ($child_id>0){
	print "telling child: kill('QUIT',$child_id)\n";
	killfam 'TERM',($child_id);
    }
    sysopen(OUT, $report, O_WRONLY|O_CREAT|O_TRUNC,0666) 
	or die "Cannot write to file: $report\n$!\n";
    print OUT "$message\n";
    print "$message\n";
    close OUT;
    exit 1;
}

my @drivers = `ps -Af|grep '[p]erl.*cmsShow.pl'`;
my %cmsShows = ();

sub findCmsShowMainWindows{
    my $lastWindowFound = "";
    foreach my $line(`xwininfo -root -all|grep 'cmsShow:'`){
	if ( my ($windowId) = ($line =~ /^\s*(\S+)/) ){
	    if (! defined $cmsShows{$windowId}){
		$lastWindowFound = $windowId; 
		$cmsShows{$windowId}++;
	    }
	}
    }
    return $lastWindowFound;
}

# starting the display
my $pid = -1;
findCmsShowMainWindows();
$pid = fork();
quit("Cannot start cmsShow. Fork failed: $!\n",0) unless defined $pid;
if ($pid == 0){
    # Begin the child process.
    print("date >> $logFile; ./cmsShow @ARGV  2>&1 >> $logFile\n");
    exec("date >> $logFile; ./cmsShow @ARGV  2>&1 >> $logFile");
    die "Failed to start the display\n";  
    # Ends the child process.
}
$SIG{HUP}  = sub { kill('HUP',$pid); };
$SIG{INT}  = sub { kill('INT',$pid); };
$SIG{QUIT} = sub { kill('QUIT',$pid); };
my $wid;
my $counter = 0;
my $warnings;
sleep 10;
while ( waitpid($pid, WNOHANG) == 0)
{
    quit("Factory mode is disabled. Abort\n",$pid) 
	unless (-e "$ENV{HOME}/factory_mode");
    sleep 1; # don't change time!
    next unless ($take_snapshots);
    # to avoid creating multiple screenshots
    # do nothing if we are not the first driver 
    next if (@drivers > 1);
    if ( ! defined $wid ){
	my $id = findCmsShowMainWindows();
	if ( $id ne "" ){
	    $wid = $id;
	    # sleep 10;
	    print("xraise $wid\n");
	    system("xraise $wid");
	} else {
	    $counter++;
	    if ($counter > $timeoutToEstablishControl){
		quit("Failed to establish monitoring for cmsShow.\n".
		     "Window \"$window_name\" is not found.\n".
		     "No screenshots are produced.\n",$pid);
	    }
	    next;
	}
    }
    # check if the machine is idling, i.e. there is no interactive user
    my $xidle = -1;
    my $counter = 0;
    do {
	sleep 1;
	if (`xidle` =~ /(\d+)/){
	    $xidle = $1;
	} else {
	    if ($counter>100){
		quit("Failed to get idle time\nNo screenshots are produced\n",$pid);
	    }
	}
	$counter++;
    } until ( $xidle >= 0 );
    next if ($timeoutToDetectUserActivity*1000 > $xidle);
    
    # check if the main window is active and raise it if it's not
    if ( `xprop -root|grep '_NET_ACTIVE_WINDOW(WINDOW):'` !~ /$wid/){
	quit("Failed to raise window $wid\nNo screenshots are produced.\n",$pid) 
	    if (system("xraise $wid"));
    }

    # check if display is sleeping to avoid messed up screenshots
    sleep 1 if (`cat /proc/$pid/status|grep State` !~ /sleeping/);
    
    if (! system("xwd -id $wid | convert - $outputtmp") &&
	-e $outputtmp &&
	! -z $outputtmp )
     {
        my $outFile =  $outputDir;
	if (($tot % 20) ==0 ){
            system("cp  $outputtmp $outFile/fw-`date +%y%m%d-%H%M`.png");
        }
        $tot++;
        system("mv $outputtmp $outputDir/live.png");
        system("/usr/sbin/tmpwatch --atime 100 $outputDir");
    }
}



exit
    
    
