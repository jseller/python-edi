import csv
from os import listdir
from os.path import isfile, join

from pythonedi.EDIConverter import EdiFile
from pythonedi.EDIMapper import EdiMapper
from pythonedi.commodity import CommodityCodes

from pythonedi.manifest import ManifestProcessor

FILEPATH = 'files/test_data/311_CARGO_5.edi'
FILEPATH = 'files/test_data/263.edi'
'''
Field correction
- add corrected number and success/failure codes to last 6 chars of l503
- put reference code descriptino in L506

'''

class TestEdiProcessing:

    def output_samples(self, manifest_dict):
        with open('files/output/samples.csv', mode='w') as employee_file:
            employee_writer = csv.writer(employee_file, delimiter='~', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            employee_writer.writerow(['Original', 'Possible matches', 'Commodity Matches'])
            for manifest_dict in manifest_dict:
                for transaction in manifest_dict.get('transactions'):
                    employee_writer.writerow([str(transaction.get('original')),str(transaction.get('possible_matches')), str(transaction.get('commodity_matches'))])

    def build_transactions(self, full_path, output_path):
        codes = CommodityCodes('files/test_data/UNCodes.csv')
        codes.load_codes()
        un_codes = codes.get_codes()
        processor = ManifestProcessor()
        manifest = processor.build_transactions(full_path, un_codes)
        if output_path:
            processor.output_manifest(manifest, output_path)
        return manifest

    def test_get_L5(self):
        manifest_dict = self.build_transactions(FILEPATH, 'files/output/')
        pass

    def test_edi_mapping(self):
        mapper = EdiMapper()
        mapper.set_segment_definition('files/edi_mapping/311_segments.csv')
        mapper.set_elment_definition('files/edi_mapping/311_elements.csv')
        elem = mapper.get_element('B2A', 1)
        assert elem.min_length == 2
        elem = mapper.get_segment('DTM')
        assert elem.max_usage == 2

    def test_322edi_mapping(self):
        mapper = EdiMapper()
        mapper.set_segment_definition('files/edi_mapping/322_segments.csv')
        mapper.set_elment_definition('files/edi_mapping/322_elements.csv')
        elem = mapper.get_element('ZC1', 1)
        assert elem.min_length == 1
        elem = mapper.get_segment('DTM')
        assert elem.max_usage == 2