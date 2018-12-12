import json
import os
import sys
import urllib2
import networkx as nx
import matplotlib.pyplot as plt
import pylab
from sets import Set

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
			
def isInList(address, plen, pairs):
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

def main():
	topology = nx.Graph()
	pairs = {}
	ASes = []
	border = Set([])
	internal = Set([])

	with open("pairings3", 'rU') as f:
		for line in f:
			pairs = json.loads(line)

	with open("ASes", 'rU') as f:
		for line in f:
			ASes.append(line.strip())

	topology.add_nodes_from(ASes)
	topology.add_node("Outside China")
	chineseASes = Set(ASes)

	with open("traceresults", 'rU') as f:
		for line in f:
			if "traceroute" not in line:
				r = isInList(line.strip(), 32, pairs)
				if r == "":
					i += 1
					queryresult = urllib2.urlopen("https://ipinfo.io/" + line.strip() + "?token=TOKEN").read()
					response = json.loads(queryresult)
					if "org" in response and response["org"] != "":
						print(response)
						AS = response["org"].split()[0]
						pairs[line.strip() + '/' + '32'] = {AS : 1}
						print(line.strip() + '/' + '32' + ':' + str(AS))
					else:
						pairs[line.strip() + '/' + '32'] = {'0' : 1}

	pairings = open("pairings3", "w")
	pairings.write(json.dumps(pairs))
	pairings.close()

	prevAS = None

	with open("traceresults", 'rU') as f:
		for line in f:
			if "traceroute" not in line:
				r = isInList(line.strip(), 32, pairs)
				ASlist = pairs[r]
				highest = 0
				AS = ''
				if len(ASlist) > 1:
					for key, val in ASlist:
						if val > highest:
							AS = key
							highest = val
				else:
					AS = ASlist.keys()[0]

				if AS in chineseASes:
					if prevAS in chineseASes:
						internal.add(AS)
						topology.add_edge(AS, prevAS)
					else:
						border.add(AS)
						topology.add_edge(AS, "Outside China")

				prevAS = AS
			else:
				prevAS = None
	for node in ASes:
		if node not in border and node not in internal:
			topology.remove_node(node)
	pos = nx.spring_layout(topology)
	print(topology.edges)
	print(internal)
	print(border)
	nx.draw(topology, pos)
	pylab.show()

if __name__ == '__main__':
	main()
