""" Parsing test cases for PythonEDI """

import json
import pprint
import pythonedi
from pythonedi.EDIParser import EDIParser
from pythonedi.EDIConverter import EdiFile, EdiParser
from pythonedi.commodity import CommodityCodes, CommodityCodeFinder
from pythonedi.commodity_matcher import DescriptionMatcher
from pythonedi.processor import ManifestProcessor

TEST_EDI = "files/test_data/263.edi" 

class TestCorrections():

    def test_correction(self):
        self.parser = pythonedi.EDIParser(TEST_EDI)
        edi_data = None
        stats = {}
        with open(TEST_EDI, "r") as test_edi_file:
            test_edi = test_edi_file.read()
            stats, edi_data = self.parser.parse(test_edi)
        corrected_codes = []
        
        codes = CommodityCodes('files/test_data/UNCodes.csv')
        codes.load_codes()
        un_codes = codes.get_codes()
        
        manifest = {'edi_data': edi_data}
        commodity_finder = CommodityCodeFinder(un_codes)
        # find codes and descriptions
        data_transactions = manifest.get('edi_data').get('TXN')
        manifest['transactions'] = []
        #print("\n\n data transactions "+str(len(data_transactions)))
        commodity_matches = 0
        for idx, transaction in enumerate(data_transactions):
            control_number = transaction.get('ST').get('ST02')
            possible = commodity_finder.find_commodites(transaction)
            corrected = commodity_finder.correct_commodity_code(transaction, possible)
            found = {'control_number': control_number, 'commodities': possible, 'corrected': corrected}
            manifest['transactions'].append(found)

    def test_processing():
        processor = ManifestProcessor()
        manifest = processor.build_transactions(full_path, un_codes, self)
        processor.output_manifest(manifest, output_path)
