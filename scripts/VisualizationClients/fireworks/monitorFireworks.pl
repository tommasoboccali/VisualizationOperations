#!/bin/env perl
#
# Created by dmytro.kovalskyi@cern.ch
#
use warnings;
use strict;
use Fcntl;

exit unless (-e "$ENV{HOME}/factory_mode");
umask 0;

my $log_file          = "$ENV{HOME}/fireworks/log/monitor.log";
my $problem_file      = "$ENV{HOME}/fireworks/status/problems";
my $cmsShow_command   = "date >> $log_file; ~/default_cmsShow >> $log_file 2>&1";
my $feeder_command    = "~/bin/eventDisplayFeeder.pl";
my $status_command    = "/afs/cern.ch/user/c/ccoffl/public/evdisp_mon/evdisp_mon_client.py -g 350x350-0-1200 2>&1 >/dev/null";
my ($processid_kde)   = (`/sbin/pidof -x  /usr/bin/startkde`=~ /(\d+)/);
my ($processid_gnome) = (`/sbin/pidof gnome-session` =~ /(\d+)/);

my $message = `date`."\trunning the monitor...\n";
# check if there is any one logged on
if ( ! $processid_kde &&  ! $processid_gnome ){
    $message .= "PROBLEM: no one is logged on scx5scr18\n";
    open(OUT, ">$problem_file")||die "Cannot open problems file for writing\n$!\n";
    print OUT $message; 
    close OUT;
    open(LOG,">>$log_file")||die "Cannot open log file for writing\n$!\n";
    print LOG $message;
    close LOG;
    exit;
} else {
    unlink $problem_file if(-e $problem_file);
}

# get environment of the running session
my $pid;
if ($processid_gnome){
    $pid = $processid_gnome;
} else {
    $pid = $processid_kde;
}
my $env = "";
foreach  my $line (split(/\0/,`cat /proc/$pid/environ`)){
    $env .= "$line;" if ( $line =~ /DISPLAY|XAUTHORITY/ );
}
$env .="export XAUTHORITY;export DISPLAY";
$env =~ s/\n/;/g;

my @pids = ();

# check if Fireworks is running, if not restart
if (`ps -Af|grep '[p]erl.*cmsShow.pl'` !~ /\S/){
    $message .= "\tFireworks was not running and has been restarted.\n";
    my $pid = fork();
    if ( $pid == 0 ){
	exec("eval \"$env\";$cmsShow_command");
	die "Failed to execute eval \"$env\";$cmsShow_command\n";
    } else {
	push @pids, $pid;
    }
}
# check if the event display feeding script is running
if (`ps -Af|grep '[p]erl.*eventDisplayFeeder.pl'` !~ /\S/){
    $message .= "\teventDisplayFeeder.pl was not running and has been restarted.\n";
    my $pid = fork();
    if ( $pid == 0 ){
	exec("$feeder_command");
	die "Failed to execute $feeder_command\n";
    } else {
	push @pids, $pid;
    }
}
# check if the status monitor is running
if (`ps -Af|grep [\/]bin\/sh.*evdisp` !~ /\S/){
    $message .= "\tevdisp was not running and has been restarted.\n";
    my $pid = fork();
    if ( $pid == 0 ){
	exec("eval \"$env\";$status_command");
	die "Failed to execute eval \"$env\";$status_command\n";
    } else {
	push @pids, $pid;
    }
}

#wait for all children to finish
for my $pid (@pids) {
    waitpid $pid, 0;
}

open(LOG,">>$log_file")||die "Cannot open log file for writing\n$!\n";
$message .= "\tdone.\n";
print LOG $message;
close LOG;

exit
