import csv, re, json

'''
codes with tilde
parse into dictionary
for any match, check matches

'''

from fuzzywuzzy import fuzz, process
from unidecode import unidecode

'''
can find rum and wine as they have patterns of weight and containers

 69 BOX,INSOLE FOTWEAR AND ACCESORIESHS CODE 848180 
 checking wrong coding:
 848180 Taps, cocks, valves and similar appliances; for pipes, boiler shells, tanks, vats or the like, including thermostatically controlled valves
'''

class Matching(object):

    def __init__(self, text):
        self.text = text
        self.matches = []

    def add(self, description, score, code):
        self.matches.append({'description':description, 'score': score, 'code': code})

    def __str__(self):
        return '%s %s %s' % (self.text, str(self.matches))

    def __dict__(self):
        #return {attr: getattr(self, attr) for attr in self.__dict__}
        return {'code':self.code}

    def to_dict(self):
        return {'text':self.text, 'matches': self.matches}

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class DescriptionMatcher:
    
    def __init__(self):
        self.commmodity_reference = {}
        with open('files/edi_mapping/untilde.csv', encoding="utf-8") as f:
            reader = csv.reader(f, delimiter='~')
            for row in reader:
                key = row[1]
                self.commmodity_reference[key] = self.clean_string(row[2])
        print('matcher loaded')
        
    def clean_string(self, column):
        if isinstance(column, list):
            column = ''.join(column)
        column = unidecode(column)
        column = re.sub('\n', ' ', column)
        column = re.sub('-', '', column)
        column = re.sub('/', ' ', column)
        column = re.sub("'", '', column)
        column = re.sub(",", '', column)
        column = re.sub(":", ' ', column)
        column = re.sub(' +', ' ', column)
        column = column.strip().strip('"').strip("'").lower().strip()
        if not column:
            column = None
        return column

    def train(self):
        #load training file
        # use uncertain pairs, and makePairs for unknowns (from user input)
        pass
    
    def find(self, text):
        if len(text) > 20:
            text = text[0:20]
        #TODO clean text for entities
        print("finding: "+text)
        ratios = process.extract(text, self.commmodity_reference)
        return ratios

    def find_match(self, text):
        found = self.find(text)
        match = Matching(text) 
        for item in found:
            match.add(item[0], item[1], item[2])
        return match
    
    def find_list(self, terms):
        found_items = []
        for text in terms:
            found_items.append(self.find_match(text))
        return found_items

