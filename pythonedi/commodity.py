import csv, logging
import re
import string
import json

HS_PATTERN = "(H+[\s]*[.]*[A-Z]*[\s]*S+[\s]*[.]*\s*[A]*[-]*[/]*[:]*)"
HC_PATTERN = "(H+[\s]*[.]*[A-Z]*[\s]*C+[\s]*[.]*\s*[-]*)"
CODE_PATTERN = "(C+O+D*E*\s*)"
HARMONIZED_PATTERN = "(HARMONIZE\s*[.]*[:]*\s*)"
CLASSIFICATION_PATTERN = "(CLASSIFICATION\s*N*O*\s*[.]*[:]*\s*)"
COMMODITY_PATTERN = "(COMMODI\s*T\s*Y\s*N*O*\s*[.]*[:]*\s*)"
CODE_NUM_PATTERN = "(C*\s*O*\s*D*\s*E*\s*N*U*M*O*S*[#]*\s*[-]*[.]*[:]*\s*)"
NC_PATTERN = "([A-Z]{3}[:])"
NUMBER_PATTERN = "(\d*[.]*[,]*\s*\d*[.]*[,]*\s*\d*[.]*[,]*\s*\d*[.]*[,]*\s*)"

class CodeMatcher(object):
    
    def __init__(self):
        combined = [
            HS_PATTERN+CODE_NUM_PATTERN+NUMBER_PATTERN,
            HC_PATTERN+CODE_NUM_PATTERN+NUMBER_PATTERN,
            HS_PATTERN+CLASSIFICATION_PATTERN+NUMBER_PATTERN,
            HS_PATTERN+NUMBER_PATTERN,
            HS_PATTERN+NC_PATTERN+NUMBER_PATTERN,
            CODE_PATTERN+NUMBER_PATTERN,
            HARMONIZED_PATTERN+CODE_NUM_PATTERN+NUMBER_PATTERN, 
            COMMODITY_PATTERN+CODE_NUM_PATTERN+NUMBER_PATTERN
        ]
        self.templates = {}
        for key in combined:
            self.templates[key] = re.compile(key, flags=re.IGNORECASE)

    def find(self, text):
        for template in self.templates.values():
            result = template.findall(text)
            for found in result:
                found_num = ''
                if len(found) == 3:
                    found_num = found[2].strip()
                if len(found) == 2:
                    found_num = found[1].strip()
                if len(found_num) > 0:
                    if ',' in found_num:
                        found_many = found_num.split(',')
                        for found_many_item in found_many:
                            found_num = found_many_item.strip()
                    return found_num


class Code(object):

    def __init__(self, code, description, parent=0, level=0, is_leaf=False):
        self.code = code
        self.description = description
        self.parent = parent
        self.level = level
        self.is_leaf = is_leaf

    def __str__(self):
        return '%s %s %s' % (self.code, self.description, self.parent)

    def __dict__(self):
        #return {attr: getattr(self, attr) for attr in self.__dict__}
        return {'code':self.code}

    def to_dict(self):
        return {'code':self.code, 'description': self.description}

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class CommodityCodes(object):

    def __init__(self, file_path):
        self.file = file_path
        self.codes = {}
    
    def load_codes(self):
        input_file = csv.DictReader(open(self.file))
        for row in input_file:
            try:
                key = int(row.get('Code'))
                self.codes[key] = Code(row.get('Code'), row.get('Description'), row.get('Code Parent'))
            except ValueError as e:
                pass

    def get_file(self):
        return self.file

    def get_codes(self):
        return self.codes


class CommodityCodeFinder(object):

    def __init__(self, codes):
        self.codes = codes
        self.found_codes = []

    def get_commodity(self, clean):
        try:
            if len(clean) > 6:
                clean = clean[0:6]
            code_num = int(clean)
            commodity = self.codes.get(code_num)
            if commodity:
                return commodity.to_dict()
        except ValueError as e:
            print(e)
            logging.error(str(e))

    def find_commodites(self, transaction):
        text_segments = transaction.get('L_LX')
        possible_code_descriptions = []
        matcher = CodeMatcher()
        for segment in text_segments:
            # get l5 for code and desc
            code_segments = segment.get('L_L0')
            if code_segments:
                for descriptions in code_segments:
                    possible = {}
                    found_descriptions = ''
                    for lading in descriptions.get('L5'):
                        if lading.get('L501') == 1:
                            found_descriptions += lading.get('L502')
                        if lading.get('L501') == 2:
                            found_descriptions += lading.get('L502')
                        if lading.get('L501') == 3:
                            found_descriptions += lading.get('L502')
                            possible['L503'] = lading.get('L502')
                    if found_descriptions:
                        possible['code_text'] = found_descriptions
                        found = matcher.find(found_descriptions)
                        if found:
                            found = found.replace('.', '')
                            possible['code'] = found
                            possible['commodity'] = self.get_commodity(found)
                    possible_code_descriptions.append(possible)
        return possible_code_descriptions

    def correct_commodity_code(self, transaction, commodity_codes):
        text_segments = transaction.get('L_LX')
        corrected = []
        for segment in text_segments:
            code_segments = segment.get('L_L0')
            for descriptions in code_segments:
                code_corrected = False
                idx = 0
                for lading in descriptions.get('L5'):
                    if lading.get('L501') == 3:
                        found = commodity_codes.pop(0) if len(commodity_codes) > 0 else None
                        if found:
                            commodity = found.get('commodity')
                            if commodity:
                                commodity['corrected'] = lading.get('L502') 
                                corrected.append(commodity)
                                lading['L502'] = commodity.get('code')
                                code_corrected = True
                if not code_corrected:
                    found = commodity_codes.pop(0) if len(commodity_codes) > 0 else None
                    if found:
                        commodity = found.get('commodity')
                        if commodity:
                            commodity['corrected'] = lading.get('L502') 
                            corrected.append(commodity)
                            descriptions['L5'].append({'L501':3, 'L502': commodity.get('code')})
        return corrected
