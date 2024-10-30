
import csv
import collections

class EdiElement(object):
    
    def __init__(self, row):
        self.segment = row.get('Segment')
        self.element = int(row.get('Element'))
        self.description = row.get('Description')
        self.required = row.get('Req')
        self.min_length = int(row.get('MinLength'))
        self.max_length = int(row.get('MaxLength'))

    def __str__(self):
        return "%s %s %s %s" % (self.segment, self.element, str(self.min_length), str(self.min_length))

    def to_dict(self):
        return {'segment': self.segment, 'element': self.element, 'description': self.description, 'required': self.required, 'min_length': self.min_length, 'max_length': self.max_length}

class EdiSegment(object):
    
    def __init__(self, row):
        self.segment = row.get('Segment')
        self.description = row.get('Description')
        self.sect = row.get('Sect')
        self.required = row.get('Req')
        self.max_usage = int(row.get('MaxUsage'))
        self.max_loop = int(row.get('MaxLoop'))
        self.pos = row.get('Pos')

    def to_dict(self):
        return {'segment': self.segment, 'description': self.description, 'sec': self.sect, 'pos': self.pos, 'required': self.required, 'max_usage': self.max_usage, 'max_loop': self.max_loop}

class EdiMapper(object):

    def __init__(self):
        self.segments = []
        self.elements = []

    def set_segment_definition(self, file_path):
        with open(file_path) as fd:
            for row in csv.DictReader(fd):
                self.segments.append(EdiSegment(row))

    def set_elment_definition(self, file_path):
        with open(file_path) as fd:
            for row in csv.DictReader(fd):
                self.elements.append(EdiElement(row))

    def get_element(self, segment, id):
        for element in self.elements:
            if element.segment == segment and element.element == id:
                return element

    def get_segment(self, id):
        for segment in self.segments:
            if segment.segment == id:
                return segment

    def to_dict(self):
        return {'segments' : [s.to_dict() for s in self.segments]}
