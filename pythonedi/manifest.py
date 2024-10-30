
import logging
import string
import json

'''
Manifest has one or more transactions
Transactions have Segments
Segments have Fields

'''
class Manifest(object):

    def __init__(self, source):
        self.source = source
        self.carrier = None
        self.stats = {}
        self.transactions = []
        self.id = 1

    def set_stats(self, stats):
        self.stats = stats

    def calculate_stats(self):
        total_matched = 0
        total_errors = 0
        for transaction in self.transactions:
            transaction.calculate_stats()
            total_matched += len(transaction.commodity_matches)
            total_errors += transaction.stats.get('errors')
        stats = {} if self.stats is None else self.stats
        stats['filename'] = self.source
        stats['transactions'] = len(self.transactions) 
        stats['commodity_matches'] = total_matched
        stats['errors'] = total_errors
        self.stats = stats
        return stats

    def add_transaction(self, transaction):
        self.transactions.append(transaction)

    def to_dict(self):
        return {'source': self.source, 
                'carrier': self.carrier,
                'stats': self.stats, 
                'transactions' : [s.to_dict() for s in self.transactions]}

class Transaction(object):
    '''
    manifest file is parsed, check for line endings and encoding, replace tilde in corrected return
    original: found in file
    actions taken: audit event
    corrected output:
    '''

    def __init__(self, source):
        self.source = source
        self.segments = []
        self.id_code = ''
        self.control_number = ''
        self.reference_number = ''
        self.original_text = ''
        self.text_segments = []
        self.possible_matches = []
        self.code_descriptions = []
        self.commodity_matches = []

    def calculate_stats(self):
        stats = {}
        stats['filename'] = self.source
        stats['commodity_matches'] = len(self.commodity_matches)
        stats['errors'] = 0
        for seg in self.segments:
            for field in seg.fields:
                if field.get('status') == 'failed':
                    stats['errors'] += 1
        self.stats = stats
        return stats

    def add_segment(self, segment):
        self.segments.append(segment)

    def get_segments(self):
        return self.segments
        
    def get_or_create_segment(self, name):
        for segment in self.segments:
            if name == segment.name:
                return segment
        segment = Segment(name)
        self.add_segment(segment)
        return segment

    def set_id_code(self, code):
        self.id_code = code

    def set_control_number(self, code):
        self.control_number = code

    def add_commodity_match(self, commodity):
        for cc in self.commodity_matches:
            if cc.code == commodity.code:
                return
        self.commodity_matches.append(commodity)

    def to_dict(self):
        possible_matches = []
        for code in self.get_possible_matches():
            possible_matches.append(code)
        return {'source': self.source,
                'id_code': self.id_code,
                'control_number': self.control_number,
                'reference_number': self.reference_number,
                'segments' : [s.to_dict() for s in self.segments],
                'original' : self.get_original_text(),
                'possible_matches': possible_matches,
                'code_descriptions': self.code_descriptions,
                'text_segments': self.text_segments,
                'commodity_matches': [cm.to_dict() for cm in self.commodity_matches]
            }

    def from_dict(self, d):
        for a, b in d.items():
            if isinstance(b, (list, tuple)):
               setattr(self, a, [self.from_dict(x) if isinstance(x, dict) else x for x in b])
            else:
               setattr(self, a, self.from_dict(b) if isinstance(b, dict) else b)

    def __str__(self):
        return str(self.to_dict())

    def get_original_text(self):
        return self.original_text

    def find_text_for_codes(self):
        # this is a list, 
        # check in 3rd element, 
        # if code in 03 its valid if none append all and search
        text_segment_index = 0
        for segment in self.segments:
            if segment.name.startswith('L0'):
                text_segment_index += 1
            text_found = []
            if segment.name.startswith('L5'):
                text = segment.items.get('GEN2')
                if text:
                    self.original_text += ''.join(text)
                    index_text = ' '+' '.join(text)
                    if len(self.text_segments) < text_segment_index:
                        self.text_segments.append(index_text)
                    else:
                        self.text_segments[text_segment_index -1] += index_text
        return self.text_segments

    def get_possible_matches(self):
        return self.possible_matches


class Segment(object):
    '''
    items (L5, R1)
    cleaned: decoding, remove stop words, change text to lower case, remove punctuation, remove bad characters.
    errors:
    schema violations:
    possible found code (text and code, gets description text for each possible code)
    possible matches (text and code, text in lookup table)
    '''

    def __init__(self, name):
        self.name = name
        self.items = {}
        self.status = 'new'
        self.fields = []

    def add_text(self, name, text):
        if text is None or len(text.strip()) == 0:
            return
        if self.items.get(name) is None:
            self.items[name] = [text]
        else:
            self.items[name].append(text)

    def add_status(self, status, segment_index, message, text):
        passed = {'status': status, 'segment_index': segment_index, 'message': message, 'text':text}
        self.fields.append(passed)

    def to_dict(self):
        item_list = []
        for key, val in self.items.items():
            item_list.append({'idx':key, 'val': val})
        return {'name':self.name,
                'items': item_list,
                'fields': self.fields}

    def __str__(self):
        return str(self.to_dict())

