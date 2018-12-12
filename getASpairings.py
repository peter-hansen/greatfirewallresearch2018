#!/usr/bin/env python
'''
print_all.py - a script to print a MRT format data using mrtparse.
Copyright (C) 2018 Tetsumune KISO
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
	http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
Authors:
	Tetsumune KISO <t2mune@gmail.com>
	Yoshiyuki YAMAUCHI <info@greenhippo.co.jp>
	Nobuhiro ITOU <js333123@gmail.com>
'''

import sys
import os
import json
from optparse import OptionParser
from datetime import *
from mrtparse import *

indt = ' ' * 4
indt_num = 0
contents = ''
pairs = {}

def prerror(m):
	print('%s: %s' % (MRT_ERR_C[m.err], m.err_msg))
	if m.err == MRT_ERR_C['MRT Header Error']:
		buf = m.buf
	else:
		buf = m.buf[12:]
	s = ''
	for i in range(len(buf)):
		if isinstance(buf[i], str):
			s += '%02x ' % ord(buf[i])
		else:
			s += '%02x ' % buf[i]

		if (i + 1) % 16 == 0:
			print('    %s' % s)
			s = ''
		elif (i + 1) % 8 == 0:
			s += ' '
	if len(s):
		print('    %s' % s)

def decreaseMask(address, plen): 
	if plen <= 1:
		return address + '/' + str(plen)
	octets = address.split(".")
	i = 0
	newAddr = [0,0,0,0]
	for i in xrange(0,plen-1):
		if (int(octets[i/8]) >> (7 - i%8))%2 == 1:
			newAddr[i/8] += 2**(7-(i%8))
	return '.'.join(str(x) for x in newAddr) + '/' + str(plen-1)
			
def isInList(address, plen, AS):
	if address + '/' + str(plen) in pairs:
		#if pairs[address + '/' + str(plen)] != AS:
		#	print "old: " + str(pairs[address + '/' + str(plen)]) + " new: " + str(AS)
		return address + '/' + str(plen)
	for x in xrange(1,plen):
		new = decreaseMask(address, plen-x)
		if new in pairs:
			#if pairs[new] != AS:
			#	print "old: " + str(pairs[new]) + " new: " + str(AS)
			return new
	return ""

		#newAddr[i/8] += int(int(octets[i/8])%(2**(7-(i%8)))) + 1

def main():
	global contents
	ASes = []
	x = 0.0
	p = 0
	if len(sys.argv) != 3:
		print('Usage: %s FILEDIRECTORY ASes' % sys.argv[0])
		exit(1)

	with open(sys.argv[2], 'rU') as f:
		for line in f:
			ASes.append(line.strip())

	for filename in os.listdir(sys.argv[1]):
		d = Reader(sys.argv[1] + "/" + filename)
		x += 1.0
		print(str(x/3096) + "%")
		p += 1

		# if you want to use 'asdot+' or 'asdot' for AS numbers,
		# comment out either line below.
		# default is 'asplain'.
		#
		# as_repr(AS_REPR['asdot+'])
		# as_repr(AS_REPR['asdot'])

		tot = 0
		for m in d:
			contents = ''
			m = m.mrt
			if m.err == MRT_ERR_C['MRT Header Error']:
				prerror(m)
				continue

			contents = ''
			if m.err == MRT_ERR_C['MRT Data Error']:
				prerror(m)
				continue
			if m.type == MRT_T['BGP4MP'] \
				or m.type == MRT_T['BGP4MP_ET']:
				if m.bgp.msg is not None:
					if m.bgp.msg.type == BGP_MSG_T['UPDATE']:
						for attr in m.bgp.msg.attr:
							if attr.type == BGP_ATTR_T['AS_PATH']:
								for path_seg in attr.as_path:
									if path_seg['type'] == 2:
										for nlri in m.bgp.msg.nlri:
											tot += 1
											length = path_seg['len']
											path = path_seg['val']
											finalas = path[length-1]
											result = isInList(nlri.prefix, nlri.plen, finalas)
											if result == '':
												pairs[nlri.prefix + '/' + str(nlri.plen)] = {finalas : 1}
											elif finalas in pairs[result]:
												pairs[result][finalas] += 1
											else:
												pairs[result][finalas] = 1

	IPs = open("IPs", "a")
	pairings = open("pairings", "w")
	i = 0.0	        		
	for key, val in pairs.items():
		for autons, occ in val.items():
			if autons in ASes:
				IPs.write(key.split("/")[0] + "\n")
		tot += 1.0
		i += len(val.keys())
	#print(pairs)
	pairings.write(json.dumps(pairs))

if __name__ == '__main__':
	main()