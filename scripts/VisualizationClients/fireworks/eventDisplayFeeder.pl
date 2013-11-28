#!/bin/env perl
#
# Created by dmytro.kovalskyi@cern.ch
#
use strict;
use warnings;
use Fcntl;

my $port = 9092;

my $keep_going = 1;
my $current_file_name = "";
while ($keep_going)
{
    exit unless ( -e "$ENV{HOME}/factory_mode");
    my $latestFile = `cat /afs/cern.ch/user/c/ccoffl/RootFileTempStorageArea/Log/LastFile`;
    $latestFile =~ s/\n//;
    if ( $latestFile ne $current_file_name && ! -e "$ENV{HOME}/pauseLiveUpdates" ){
	system("echo $latestFile | nc -w 10 localhost $port");
	$current_file_name = $latestFile;
	system("echo $current_file_name > ~/current_datafile.txt");
    }
    sleep 10;
}
exit
