#!/bin/bash
while read p; do
	echo "traceroute $p"
	traceroute -n -q 1 $p | grep -o '[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}'
done < IPs