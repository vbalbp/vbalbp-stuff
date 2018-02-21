#load libraries
# trying stuff
import xml.etree.ElementTree as ET

#function that will read the tree and make the corresponding changes
def change_to_FFT(branch):
	for child in branch.findall('{http://www.loc.gov/MARC21/slim}datafield'):
		#we change the attribute's name
		if child.attrib["tag"] == "856":
			child.attrib["tag"] = "FFT"
			child.attrib["ind1"] = " "
		#and we change the attributes of the children of each datafield
		for grandchild in child:
			#in case that some instance is not full, we fill it ourselves
			if len(child) == 1:
				new = ET.Element('subfield')
				new.text='Fulltext'
				new.attrib["code"] = 'd'
				child.append(new)
				new = ET.Element('subfield')
				new.text='INSPIRE-PUBLIC'
				new.attrib["code"] = 't'
				child.append(new)
			#we change the values to match what we want
			if grandchild.attrib["code"] == "u":
				grandchild.attrib["code"] = "a"
			if grandchild.attrib["code"] == "w":
				grandchild.attrib["code"] = "d"
				grandchild.text = "Fulltext"
			if grandchild.attrib["code"] == "y":
				grandchild.attrib["code"] = "t"
				grandchild.text = "INSPIRE-PUBLIC"


#main function, we read the file
tree = ET.parse('thingy.xml')
#load it as a tree with our library
ET.register_namespace('',"http://www.loc.gov/MARC21/slim")
root = tree.getroot()
#and execute the function for ech child
for child in root:
	change_to_FFT(child)

#we write the output
tree.write('output.xml',xml_declaration = True)