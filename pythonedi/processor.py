import logging
import json
from os import listdir
from os.path import isfile, join

from pythonedi import EDIParser, EDIGenerator

from .EDIConverter import EdiFile, EdiParser
from .commodity import CommodityCodes, CommodityCodeFinder


class ManifestProcessor(object):

    def get_text_matches(self, transaction):
        for pm in transaction.possible_matches:
            text_segments = pm.get('descriptions')
            if text_segments:
                logging.info('matching text for: '+str(text_segments))
                match = matcher.find_match(text_segments[0])
                transaction.found_descriptions.append(match.to_dict())

    def get_data_from_source(self, path):
        #convert the file
        ef = EdiFile(path)
        converted = ef.get_converted_file()
        return converted

    def parse_edi(self, source):
        self.parser = EDIParser(source)
        with open(source, "r") as edi_file:
            data = edi_file.read()
            return self.parser.parse(data)

    def process_manifest(self, manifest, un_codes, task):
        commodity_finder = CommodityCodeFinder(un_codes)
        # find codes and descriptions
        transactions = manifest.get('edi_data').get('TXN')
        carrier_date = manifest.get('edi_data').get('GS').get('GS02') + '-' + manifest.get('edi_data').get('GS').get('GS04')
        manifest['transactions'] = []
        for idx, transaction in enumerate(transactions):
            control_number = transaction.get('ST').get('ST02')
            possible = commodity_finder.find_commodites(transaction)
            # check if possible has a L503 field filled\
            # correct filed wiht transaction            
            #print(str(possible))
            corrected = commodity_finder.correct_commodity_code(transaction, possible)
            # if not possible code, get descripiton matches
            #if not corrected:
            #self.get_text_matches(transaction)
            found = {'control_number': control_number, 'carrier_date' : carrier_date, 'corrected': corrected}
            manifest['transactions'].append(found)
            if task:
                task.update_state(state='PROGRESS',
                              meta={'current': idx, 'total': len(transactions),
                                    'status': 'processing transaction '+control_number})
        return manifest

    def build_transactions(self, full_path, un_codes, task=None):
        stats, edi_data = self.parse_edi(full_path)
        manifest = {}
        manifest['stats'] = stats
        manifest['edi_data'] = edi_data
        return self.process_manifest(manifest, un_codes, task)

    def set_manfest_stats(self, manifest):
        transaction_stats = []
        for idx, transaction in enumerate(manifest.get('transactions')):
            stats = {}
            stats['control_number'] = transaction.get('control_number')
            stats['corrected'] = transaction.get('corrected')
            stats['fields'] = len(transaction.get('status'))
            transaction_stats.append(stats)
        manifest['stats']['transactions'] = transaction_stats

    def output_manifest(self, manifest, output_path):
        stats = manifest.get('stats')
        full_path = stats.get('source')
        file_name = full_path[full_path.rfind('/')+1:len(full_path)]
        # EDI Generator for ourput and validation
        generator = EDIGenerator(element_delimiter= stats.get('element_delimiter'), segment_delimiter=stats.get('segment_delimiter'))
        manifest = generator.build(manifest)
        stats['total_segments'] = generator.total_segments
        stats['total_errors'] = generator.total_errors
        self.set_manfest_stats(manifest)
        print(str(manifest))
        file_path = output_path + file_name + '_corrected.edi'
        with open(file_path, 'w') as open_file:
            open_file.write(manifest['out_file'])