import itertools
import requests
from lxml import etree
import re

# function to generate the records
def obtain_records():
	url = 'http://inspirehep.net/search'
	jrec = 1
	query = 'r slac-pub-* and not 8564:*inspirehep*pdf'
	cookie = {'_pk_id.8.b7b7' : 'b4c037ee7153df89.1517494716.3.1517817000.1517815770.', '_pk_ref.9.b7b7' : "%5B%22%22%2C%22%22%2C1517815770%2C%22https%3A%2F%2Fmmm.cern.ch%2Fowa%2Fredir.aspx%3FC%3DDAsFb1B23iMkPc_8X2itNN9cMGp4oTvtfJCoRDXvkR5BRKawfGnVCA..%26URL%3Dhttps%3A%2F%2Finspirehep.net%2Fyouraccount%2Fedit%3Fln%3Den%22%5D", '_pk_ses.8.b7b7' : '*', 'INVENIOSESSIONstub' : 'HTTPS' , 'INVENIOSESSION' : '051013498afc0f6731ef5532c154eed3'}
	# we loop indefinitely through the records with a stop condition inside the loop
	while(True):
		# perform the request
		results = requests.get(url, params={'wl': 0, 'rg': 250,'p': query,'of': 'xm','jrec': jrec,'cc': 'HEP','ot': '1,037'}, cookies = cookie)
		# check that we actually got a response; repeat otherwise
		while '502 Proxy Error' in results.text:
			print "Retrying..."
			results = requests.get(url, params={'wl': 0, 'rg': 250,'p': query,'of': 'xm','jrec': jrec,'cc': 'HEP','ot': '1,037'}, cookies = cookie)
		# we open a file to keep track of what is hapenning
		f = open('log.txt','w')
		f.write((results.text).encode('utf-8'))
		f.close()
		# we convert the result of the webpage to a tree structure in pyhton with lxml
		root = etree.fromstring((results.text).encode('utf-8'))
		# break condition; no results returned
		if len(root) == 0:
			break
		# we enter two levels inside the tree and check if we want the record
		for child in root:
			for grandchild in child:
				if grandchild.tag == '{http://www.loc.gov/MARC21/slim}controlfield':
					# we store the ID of the record
					cf = grandchild.text
				if grandchild.tag == '{http://www.loc.gov/MARC21/slim}datafield':
					for son in grandchild:
						if son.tag == '{http://www.loc.gov/MARC21/slim}subfield' and 'SLAC-PUB' in son.text:
							if 'SLAC-PREPRINT' in son.text:
								# we store the SLAC number in case that it is written as 'SLAC-PREPRINT'
								number = son.text[15:]
							else:
								# we store the SLAC number
								number = son.text
			jrec += 1
			# we generate the ID and the SLAC number with the generator
			yield cf, number

# we create a new tree
root = etree.Element('xml')
doc = etree.ElementTree(root)
# we call the generator
records = obtain_records()
# we iterate over the generator
for r,n in records:
	# we make sur etha tthere are no letters in the SLAC number, which could lead to a problem
	ser = re.search('[a-zA-Z]',n.split('-')[2])
	if ser == None:
		# we generate the link of the SLAC pdf
		dividendo = int(n.split('-')[2])/250
		interval = dividendo * 250
		url = 'http://slac.stanford.edu/pubs/slacpubs/' + str(interval) + '/' + n.lower() + '.pdf'
		# we check that the pdf we generated actually exists
		req = requests.get(url)
		if req.status_code == 200:
			# we create the necessary tree structure in our XML file
			rec = etree.SubElement(root, 'record')
			ctrl = etree.SubElement(rec, 'controlfield', tag = '001')
			ctrl.text = r
			dta = etree.SubElement(rec, 'datafield', tag = 'FFT', ind1 = ' ', ind2 = ' ')
			subf1 = etree.SubElement(dta, 'subfield', code = 'a')
			subf1.text = url
			subf2 = etree.SubElement(dta, 'subfield', code = 'd')
			subf2.text = 'Fulltext'
			subf3 = etree.SubElement(dta, 'subfield', code = 't')
			subf3.text = 'INSPIRE-PUBLIC'

outFile = open('homemade.xml','w')
doc.write(outFile) 
