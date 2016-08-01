"""
Created by: Nicolas Mechulam, Damian Salvia
"""

# Needs to install tweepy for python 2.7 (pip install tweepy)
import tweepy
import json
import time
import codecs
import io
import argparse
import re
import requests
import demjson

# Get parameters from command line
# graph -
# parser = argparse.ArgumentParser(description='Gets graph structure for Gephi')
# parser.add_argument('fnameDat', metavar='datFile', type=str,
                    # help='The *.dat file')
# parser.add_argument('fnameFav', metavar='favFile', type=str,
                    # help='The *.fav file which contains the comment text')
# parser.add_argument('fnameGml', metavar='gmlFile', type=str,
                    # help='The *.gml file which contains the Twecoll graph structure')

# args = parser.parse_args()
# print args.accumulate(args.fnameGml)

fnameGml = "movieuy.gml"
fnameFav = "movieuy.fav"
fnameMov = "movies.in"

def GetData(filename):
	with open(filename) as f:
		text = f.read()

		pattern = re.compile(r'id (.*)\n\s*user_id \"(.*)\"(?:(?:\n|.)*?)label \"(.*)\"(?:(?:\n|.)*?)followers (.*)(?:(?:\n|.)*?)', re.IGNORECASE)
		nodes = pattern.findall(text)

		pattern = re.compile(r'source (.*)(?:(?:\n|.)*?)target (.*)', re.IGNORECASE)
		edges = pattern.findall(text)

		# ver bien (Es una especie de join, pero no es muy eficiente, quizas hasta se pueda hacer en un paso)
		res= [(row1[1], row2[1]) for row1 in nodes for row2 in edges if row1[0]==row2[0]]
		res2= [(row2[0], row1[1]) for row1 in nodes for row2 in res if row1[0]==row2[1]]

	return nodes, res2

def GetMovieNodes(filename):
	with open(filename) as f: # Open movie names files
		movies = f.read().lower().splitlines()
		return [("Mov%i"%id,name) for id,name in zip(range(len(movies)),movies)]

def Analyze(tweet):
    url = "http://api.meaningcloud.com/sentiment-2.1"
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    payload = "key=b9e045d401c8cff464a77b9a8214a917&lang=es&txt="+tweet+"&model="
    response = requests.request("POST", url, data=payload, headers=headers)
    return response

def GetMovieEdges(fnameFav, movie_nodes):
	with open(fnameFav) as fFav: # Open tweets file
		text = fFav.read()

	movies_pattern = [(movid,re.compile(movie.replace(" ","\\s*"))) for movid,movie in movie_nodes] # Generate simple patter as hastag style

	pattern = re.compile(r'\d+\s*(.{30})\s*(\d+)\s+\@([^\s]*)\s+(.*)', re.IGNORECASE)
	data = pattern.findall(text)

	edges = []
	for date, usrid, username , tweet in data:
		for movid, pattern in movies_pattern:
			if re.search(pattern,tweet):
				# raw_input()
				resultado = Analyze(tweet)
				json = demjson.decode(resultado.text)#Decodificar la respuesta JSON
				estado = json['status']['code'];#Obtener el codigo de estado de la respuesta
				if estado == '104':
					print "Error 104 se excedio el limite de 2 solicitudes/segundo, esperando 5 segundos..."
					time.sleep( 5 )
				elif estado != '0':#Ocurrio otro tipo de error
					print "Ocurrio un ehrror "+str(estado)+", saliendo..."
					sys.exit(0);
				else:#Respuesta correcta
					edges.append((usrid,movid,username,json['score_tag']))

	return edges

def generateGraph(filename, users,movies, user_edges, movie_edges):
	with open(filename,"w") as f:
		f.write('graph\n[\n')

		# 		for node in nodes[:10]:
		# 	f.write('\tnode\n\t[\n\t\tid\n\t\tuser_id B\n\t]\n' % node[0])

		# for edge in edges[:10]:
		# 	f.write('\tedge\n\t[\n\t\tsource A\n\t\ttarget B\n\t]\n')
		#
		for node in users:
			f.write(
	'''	node
	[
		id "%s"
		label "%s"
		type "user"
		followers %s
	]
''' % (node[1], node[2], node[3]))

		for node in movies:
			f.write(
		'''	node
	[
		id "%s"
		label "%s"
		type "movie"
	]
''' % (node[0], node[1]))

		for edge in user_edges:
			f.write(
	'''	edge
	[
		source "%s"
		target "%s"
		type "relation"
	]
''' % (edge[0],edge[1])
			)

		for edge in movie_edges:
			f.write(
	'''	edge
	[
		source "%s"
		target "%s"
		label "%s"
		type "comment"
	]
''' % (edge[0],edge[1],edge[3])
			)
		f.write(']')

def addNodesFromFav(nodes, edges):
	idList = [node[1] for node in nodes]
	newNodes = [(0,edge[0],edge[2],0) for edge in edges if not (edge[0] in idList)]
	nodes.extend(newNodes)

def removeInactiveNodes(nodes, edges):
	print 'pending' #TODO: no se si queremos hacer esto



user_nodes, user_edges = GetData(fnameGml)
movie_nodes = GetMovieNodes(fnameMov)
# nodes = user_nodes + movie_nodes
movie_edges = GetMovieEdges(fnameFav, movie_nodes)
# edges = user_edges + movie_edges

addNodesFromFav(user_nodes, movie_edges)

removeInactiveNodes(user_nodes, movie_edges)

generateGraph('graph.gml',user_nodes,movie_nodes,user_edges,movie_edges)

print 'Success'
