import os
import json
import math
import random
import HTMLParser

from wiki_mongo import MongoDbClient, getMongoClient

from pprint import pformat


def getConfig():
	with open('config/config.json') as jsonfile:    
		data = json.load(jsonfile)
	return data


def lerp(val, minv, maxv):
	return (val - minv) / (maxv - minv)

def getSigmaNode(page, i, limit):
	views = page['views']
	radius = 1
	if views < avg:
		radius += int(lerp(views, vmin, avg) * 4)
	else:
		radius += int(lerp(views, avg, vmax) * 4)
	# print page['views'], radius
	if 'links' in page.keys():
		sigma_links[page['pid']] = page['links']
	node = {
		'id': '%d' % page['pid'],
		'label': '%s (views: %d)' % (page['title'], page['views']), # parser.unescape(page),
		'x': math.sin(math.pi * 2 * i / limit + 1),
		'y': math.cos(math.pi * 2 * i / limit + 1),
		'size': radius
	}
	return sigmanodes, parsed_ids
	

lang='en'
config = getConfig()
dbconfig = config.get('mongoDB')
mongo = getMongoClient(dbconfig)

basedir = os.path.dirname(__file__)
dest = os.path.join(basedir, '..', 'javascript','sketches', 'data')
outjson = 'wiki_sample_network.json'
rawpath = os.path.join(basedir, 'dump', 'medicine_en.json')

radius = 1
vmin = 150000
vmin = mongo.db.find_one({"views": {"$gt": vmin}}, sort=[("views", 1)])["views"]
vmax = mongo.db.find_one({"views": {"$gt": vmin}}, sort=[("views", -1)])["views"]
# avg = mongo.db.find_one({"views": {"$avg": True}})
avgCursor = mongo.db.aggregate([{'$group':{'_id':None, 'average':{'$avg':"$views"}}}])
for node in avgCursor:
	avg = node['average']
	break

# gap = (vmax - vmin) / 5
# print vmin, vmax, avg
parsed_ids = []
sigma_links = {}
sigmajson = {
	'nodes': [],
	'edges': []
}

pages = mongo.find(
	kargs={
		"lang": "en",
		"pid": {
			"$gt": 0
		},
		"views": {
			"$gt": vmin
		}
	} #, limit=100
)
# parser = HTMLParser.HTMLParser()
print 'found %d results' % pages.count()

for i, page in enumerate(pages):
	if not i % 100:
		print i
	if page['pid'] in parsed_ids:
		print "Skipped duplicate:", page['pid']
		continue
	parsed_ids = []
	sigmanodes = []
	sigmanode, parsed_id = getSigmaNode(page, i, pages.count())
	sigmajson['nodes'].append(sigmanode)
	parsed_ids.append(parsed_id)

pages = mongo.find(
	kargs={
		"lang": "en",
		"pid": {
			"$gt": 0
		},
		"links": {
			"$exists": True
		}
	} #, limit=100
)
limit = pages.count()
# parser = HTMLParser.HTMLParser()
print 'found %d results' % pages.count()
for i, page in enumerate(pages):
	if not i % 100:
		print i
	if page['pid'] in parsed_ids:
		print "Skipped duplicate:", page['pid']
		continue
	parsed_ids = []
	sigmanodes = []
	sigmanode, parsed_id = getSigmaNode(page, i, pages.count())
	sigmajson['nodes'].append(sigmanode)
	parsed_ids.append(parsed_id)


for pid, links in sigma_links.iteritems():
	for j, link in enumerate(links):
		if link in parsed_ids:
			edge = {
				'id': '%de%d' % (j, pid),
				'source': '%d' % pid,
				'target': '%d' % link
			}
			sigmajson['edges'].append(edge)

with open(os.path.join(dest, outjson), 'w') as outjsonfile:
	json.dump(sigmajson, outjsonfile, indent=1)
