
import csv
import json

class EdiSegment(object):
    
    def __init__(self, row):
        self.segment = row.get('Segment')
        self.description = row.get('Description')
        self.sect = row.get('Sect')
        self.required = row.get('Req')
        self.max_usage = int(row.get('MaxUsage'))
        self.max_loop = int(row.get('MaxLoop'))
        self.pos = row.get('Pos')
        self.elements = []

    def to_dict(self):
        element_list = []
        for elem in self.elements:
            element_list.append(elem.to_dict())
        return {'id': self.segment, 'type': 'segment', 'name': self.description, 
                        'sec': self.sect, 'pos': self.pos,'req': self.required, 
                        'max_uses': self.max_usage, 'max_loop': self.max_loop,
                        'elements' : element_list}

class EdiElement(object):
    
    def __init__(self, row):
        self.segment = row.get('Segment')
        self.element = row.get('Element')
        self.description = row.get('Description')
        self.required = row.get('Req')
        self.min_length = int(row.get('MinLength'))
        self.max_length = int(row.get('MaxLength'))
        self.data_type = row.get('Type')
        self.data_type_ids = None

    def __str__(self):
        return "%s %s %s %s" % (self.segment, self.element, str(self.min_length), str(self.min_length))

    def to_dict(self):
        length = {'min': self.min_length, 'max': self.max_length}
        the_id = self.segment 
        the_id += self.element if len(self.element) == 2 else '0' + self.element
        return {'id': the_id, 'type': 'element', 'name': self.description,
                            'req': self.required, 'length': length,
                            'data_type': self.data_type, 'data_type_ids': self.data_type_ids}

class EDISchemaJsonGenerator:

    def __init__(self, edi_format, segment_delimiter="~"):
        self.edi_format = edi_format
        self.segment_delimiter = segment_delimiter
        self.doc = {}
        self.segments = []
        self.elements = []

    def add_segments(self, csv_data):
        with open(csv_data, "r") as cdata:
            for row in csv.DictReader(cdata):
                seg = EdiSegment(row)
                self.segments.append(seg)
    
    def add_elements(self, csv_data):
        with open(csv_data, "r") as cdata:
            for row in csv.DictReader(cdata):
                elem = EdiElement(row)
                self.elements.append(elem)

    def to_dict(self):
        ret = []
        for seg in self.segments:
            for elem in self.elements:
                if seg.segment == elem.segment:     
                    seg.elements.append(elem)
            ret.append(seg.to_dict())
        return ret

    def to_json(self):
        return json.dumps(self.to_dict())