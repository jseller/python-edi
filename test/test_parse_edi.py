""" Parsing test cases for PythonEDI """

import pprint
import pythonedi

from pythonedi.EDIParser import EDIParser
from pythonedi.EDISchema import EDISchemaJsonGenerator
from pythonedi.EDIGenerator import EDIGenerator

TEST_EDI = "files/test_data/263.edi"

class TestParse810():

    def test_parse(self):
        self.parser = EDIParser("files/test_data/test_edi.txt") 
        with open("files/test_data/test_edi.txt", "r") as test_edi_file:
            test_edi = test_edi_file.read()
            found_segments, edi_data = self.parser.parse(test_edi)
            #print("Found segments: {}".format(found_segments))
            #pprint.pprint(edi_data)

    def test_parse311(self):
        self.parser = EDIParser(TEST_EDI)
        edi_data = None
        test_edi = None
        stats = {}
        with open(TEST_EDI, "r") as test_edi_file:
            test_edi = test_edi_file.read()
            stats, edi_data = self.parser.parse(test_edi)
        generator = EDIGenerator(element_delimiter= stats.get('element_delimiter'), segment_delimiter=stats.get('segment_delimiter'))
        manifest = {}
        manifest['edi_data'] = edi_data
        manifest['stats'] = {}
        manifest = generator.build(manifest)
        out_file = manifest.get('out_file')
        with open('files/output/testedi.edi', mode='w') as e_file:
            e_file.write(out_file)

    def test_generate_json_from_schema(self):
        print('test schema parsing')
        self.generator = EDISchemaJsonGenerator(edi_format="311", segment_delimiter="~")
        self.generator.add_segments('pythonedi/schema/311_segments.csv')
        self.generator.add_elements('pythonedi/schema/311_elements.csv')
        out_json = self.generator.to_dict()
        #print("{}".format(out_json))
