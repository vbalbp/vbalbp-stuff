import re
import sys
import os
import json
import requests
import unidecode

# function to calculate Levenshtein distance
def LD(s1, s2):
    if len(s1) < len(s2):
        return LD(s2, s1)
    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1       # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def map_journal_title(string):
	mini = 0
	mini_value = LD(string,'Phys.Rev.Lett.')
	if LD(string,'Phys.Rev.C.') < mini_value:
		mini = 1
		mini_value = LD(string,'Phys.Rev.C')
	if LD(string,'Phys.Rev.B.') < mini_value:
		mini = 2
		mini_value = LD(string,'Phys.Rev.B')
	if LD(string,'Phys.Rev.A.') < mini_value:
		mini = 3
		mini_value = LD(string,'Phys.Rev.A')
	if LD(string,'Phys.Rev.E.') < mini_value:
		mini = 4
		mini_value = LD(string,'Phys.Rev.E')	
	if LD(string,'Phys.Rev.D.') < mini_value:
		mini = 5
		mini_value = LD(string,'Phys.Rev.D')
	if mini == 1:
		return 'Phys.Rev.C.'
	if mini == 2:
		return 'Phys.Rev.B.'
	if mini == 3:
		return 'Phys.Rev.A.'
	if mini == 4:
		return 'Phys.Rev.E.'
	if mini == 5:
		return 'Phys.Rev.D.'
	if mini == 0:
		return 'Phys.Rev.Lett.'


# function to remove special characters and make everything lowercase for easier comparisons
def normalize_string(string):
	string = string.lower()
	string = ''.join(e for e in string if e.isalnum())
	return unidecode.unidecode(string).encode('utf-8')


# we parse the authors returned by crossreference to store them
# as a list of authors, in which each author is represented by a list with each of his names
def parse_authors(jauthors):
	new_authors = []
	author_names = []
	for author in jauthors:
		author_names += author["family"].split()
		if "given" in author:
			author_names += author["given"].split()
		new_authors.append(author_names)
		author_names = []
	for i in range(len(new_authors)):
		for j in range(len(new_authors[i])):
			new_authors[i][j] = normalize_string(new_authors[i][j])
	return new_authors

# function to parse the crossref API response
def parse_crossref_object(file_name):
	if os.stat(file_name).st_size == 0:
		print file_name + ' is empty. DOI error.'
		sys.exit()

	jsobject = json.load(open(file_name))

	title = normalize_string(jsobject["message"]["title"][0])

	pubinfo = {}
	pubinfo["journal"] = map_journal_title(str(jsobject["message"]["short-container-title"]))
	if "volume" in jsobject["message"]:
		pubinfo["volume"] = str(jsobject["message"]["volume"])
	else:
		pubinfo["volume"] = ""
	if "page" in jsobject["message"]:
		pubinfo["page"] = str(jsobject["message"]["page"]).replace('-',' ').split()[0]
	else:
		pubinfo["page"] = ""
	if "date-parts" in jsobject["message"]["issued"]:
		pubinfo["year"] = str(jsobject["message"]["issued"]["date-parts"][0][0])
	else:
		pubinfo["year"] = ""

	authors = parse_authors(jsobject["message"]["author"])

	return title, pubinfo, authors

# returns a score of either 0 or 1
# 0 means they are different
# 1 means thay are the same
# a 0 indicates directly that both records are different without further comparisons
def compare_pubinfo(pubinfo1,pubinfo2):
	score = 1
	for key in pubinfo1:
		if pubinfo1[key] != pubinfo2[key] and pubinfo1[key] != "" and pubinfo2[key] != "":
			score = 0
	return score

def compare_authors(authors1,authors2):
	results = []
	for auth1 in authors1:
		maxi = 0
		for auth2 in authors2:
			score = compare_names(filter(None,auth1), filter(None,auth2))
			if score > maxi:
				maxi = score
		results.append(maxi)
	return float(sum(results))/min(len(authors1),len(authors2))


# given two lists of the names of ONE author
# returns a real value between 0 and 1 of how much they ressemble
def compare_names(authors1,authors2):
	score = 0.0
	for auth1 in authors1:
		if len(auth1) == 1:
			for auth2 in authors2:
				if auth1 == auth2[0]:
					score += 1
					break
		else:
			for auth2 in authors2:
				if len(auth2) == 1:
					if auth1[0] == auth2:
						score += 1
						break
				else:
					if auth1 == auth2:
						score += 1
						break
	return score/min(len(authors1),len(authors2))

# function that gives us a real number between 0 and 1
# this number represents how much the titles are alike
def compare_titles(title1,title2):
	return 1 - float(LD(title1,title2))/max(len(title1),len(title2))

# function that determine sif two records are the same or not
# True: they are the same
# False: they are not
def is_it_the_same_record(record1, record2):
	score1 = compare_titles(record1[0],record2[0])
	score2 = compare_pubinfo(record1[1],record2[1])
	score3 = compare_authors(record1[2],record2[2])
	if score2 == 0:
		return False
	elif score1 < 0.4:
		return False
	elif score3 < 0.6:
		return False
	else:
		return True

# function to make the request to the isnpire API and parse the result
def parse_inspirehep_object(control_number,err):
	r = requests.get('https://inspirehep.net/record/' + control_number + '?of=recjson')
	jsobject = json.loads(r.text)
	
	title = normalize_string(jsobject[0]["title"]["title"])

	if err:
		if type(jsobject[0]["publication_info"]) == list:
			extracted_info = jsobject[0]["publication_info"][1]
		else:
			extracted_info = jsobject[0]["publication_info"]
	else:
		if type(jsobject[0]["publication_info"]) == list:
			extracted_info = jsobject[0]["publication_info"][0]
		else:
			extracted_info = jsobject[0]["publication_info"]

	pubinfo = {}
	if "title" in extracted_info:
		jtitle = str(extracted_info["title"])
	else:
		jtitle = ""
	if "volume" in extracted_info:
		jvolume = str(extracted_info["volume"])
	else:
		jvolume = ""
	if 'A' in jvolume:
		jvolume = jvolume.replace('A','')
		jtitle += 'A.'
	if 'B' in jvolume:
		jvolume = jvolume.replace('B','')
		jtitle += 'B.'
	if 'C' in jvolume:
		jvolume = jvolume.replace('C','')
		jtitle += 'C.'
	if 'D' in jvolume:
		jvolume = jvolume.replace('D','')
		jtitle += 'D.'
	if 'E' in jvolume:
		jvolume = jvolume.replace('E','')
		jtitle += 'E.'
	if 'Lett' in jvolume:
		jvolume = jvolume.replace('Lett','')
		jtitle += 'Lett.'
	pubinfo["journal"] = map_journal_title(jtitle)
	pubinfo["volume"] = jvolume
	if "pagination" in extracted_info:
		pubinfo["page"] = str(extracted_info["pagination"]).replace('-',' ').split()[0]
	else:
		pubinfo["page"] = ""
	if "year" in extracted_info:
		pubinfo["year"] = str(extracted_info["year"])
	else:
		pubinfo["year"] = ""
	
	authors = []
	names = []
	for author in jsobject[0]["authors"]:
		names = author["full_name"].replace("."," ").split()
		for i in range(len(names)):
			names[i] = normalize_string(names[i])
		authors.append(names)
		names = []

	return title, pubinfo, authors


if __name__ == "__main__":
	record_id = sys.argv[1].replace("_"," ").replace('.',' ').split()[0]
	print record_id
	cross_title, cross_pubinfo, cross_authors = parse_crossref_object(sys.argv[1])
	if cross_title[:7] == "erratum":
		inspire_title, inspire_pubinfo, inspire_authors = parse_inspirehep_object(record_id,True)
	else:
		inspire_title, inspire_pubinfo, inspire_authors = parse_inspirehep_object(record_id,False)

	cross = [cross_title, cross_pubinfo, cross_authors]
	inspirehep = [inspire_title, inspire_pubinfo, inspire_authors]

	if is_it_the_same_record(cross,inspirehep):
		print record_id + " is good."
	else:
		print record_id + " is bad."