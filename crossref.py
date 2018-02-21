import requests
import csv
import json
import time
from pathlib import Path

dois = []
ids = []
with open('phys_output.csv','r') as csvfile:
	spamreader = csv.reader(csvfile, delimiter = '\t', quotechar = '|')
	for i, row in enumerate(spamreader):
		if row[1] != '\N':
			ids.append(row[0])
			dois.append(json.loads(row[1]))


results = []
current = 0
j = 0
errors = open('errors.txt', 'w')
for elem in dois:
	for doi in elem:
		if j > 27537:
			time.sleep(0.01)
			while(True):
				try:
					r = requests.get('https://api.crossref.org/works/' + doi["value"] + '?mailto=victor.balbuena.pantigas@cern.ch')
					break
				except requests.exceptions.ConnectionError as e:
					print ('An error ocurred; retrying')
			file_path = ids[j] + '.json'
			_file = Path(file_path)
			k = 1
			while _file.is_file():
				k += 1
				file_path = ids[j] + '_' + str(k) + '.json'
				_file = Path(file_path)
			outfile = open(file_path, 'w')
			print "Creating file " + file_path
			log = open('log.txt', 'w')
			log.write(r.text)
			log.close()
			if r.text != 'Resource not found.':
				json.dump(json.loads(r.text), outfile)
			else:
				errors.write(doi["value"] + '\n')
			time.sleep(2)
	j += 1

errors.close()
		
