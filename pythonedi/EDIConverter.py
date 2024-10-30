
from badx12 import Parser
import pprint
import threading
import sys
import traceback

from .manifest import Manifest, Transaction, Segment
from .EDIMapper import EdiMapper

WINDOWS_LINE_ENDING = '\r\n'
UNIX_LINE_ENDING = '\n'
MAC_LINE_ENDING = '\r'

class EdiFile(object):

    def __init__(self, path):
        self.path = path

    def file_contents(self):
        with open(self.path, 'r', encoding='utf-8') as open_file:
            return open_file.read().strip()
        
    def convert_crlf_tilde(self, content):
        win = content.replace(WINDOWS_LINE_ENDING, '~')
        return win.replace(UNIX_LINE_ENDING, '~')

    def get_converted_file(self):
        return self.convert_crlf_tilde(self.file_contents())

    def convert_file(self, file_path):
        with open(file_path, 'rb') as open_file:
            content = open_file.read()
        content = content.replace(WINDOWS_LINE_ENDING, b'~')
        file_path = 'conv'+file_path
        with open(file_path, 'wb') as open_file:
            open_file.write(content)

class EdiParser(object):
    
    def __init__(self, source):
        self.parser = Parser()
        self.source = source.replace('.','-')

    def get_document(self, edi_file):
        self.parser.document_text = (edi_file)
        self.parser._parse_interchange_header()
        self.parser._separate_and_route_segments()
        return self.parser.document

    # build dictionary with other fields for l5 (gen4, gen5) and R4
    def parse_edi(self, edi_file):
        document = self.get_document(edi_file)
        interchange = document.to_dict().get('document').get('interchange')
        current = 'ISA'
        return_list = []
        stats = {'items':0, 'body':0, 'body_body':0}
        manifest = Manifest(self.source)
        items = interchange.get('body')
        for item in items:
            stats['items'] += 1
            reference_number = []
            for doc_field in item.get('header').get('fields'):
                header_name = doc_field.get('name')
                if header_name == 'GS02':
                    manifest.carrier = doc_field.get('content')
                    reference_number.append(doc_field.get('content'))
                if header_name == 'GS03' or header_name == 'GS04' or header_name == 'GS05':
                    reference_number.append(doc_field.get('content'))
            for body in item.get('body'):
                transaction = Transaction(self.source)
                stats['body'] += 1
                L0_index = 0
                header = body.get('header')
                #print(str(body)+str('\n\n'))
                for field in header.get('fields'):
                    header_name = field.get('name')
                    if header_name == 'ST01':
                        transaction.set_id_code(field.get('content'))
                    if header_name == 'ST02':
                        control_number = field.get('content')
                        ref = '_'.join(reference_number)
                        transaction.reference_number = ref
                        transaction.set_control_number(control_number)
                for segment_idx, body_body in enumerate(body.get('body'), start=1):
                    segment = None
                    stats['body_body'] += 1
                    #print(str(body_body)+str('\n\n'))
                    content = None
                    for idx, field in enumerate(body_body.get('fields')):
                        content = field.get('content')
                        fname = field.get('name')
                        if fname == 'GEN0':
                            current = content
                            if current == 'L0':
                                L0_index = L0_index + 1
                        elif fname == 'GEN1':
                            segment_name = current
                            if current == 'N9':
                                if not transaction.reference_number:
                                    transaction.reference_number = content
                            if current == 'L5':
                                segment_name = current+'_'+str(L0_index)+'_'+content
                            if current == 'L0':
                                segment_name = current+'_'+str(L0_index)
                            segment = transaction.get_or_create_segment(segment_name)
                            segment.add_text(fname, content)
                        else:
                            segment.add_text(fname, content)
                return_list.append(transaction)
                manifest.add_transaction(transaction)
        manifest.set_stats(stats)
        return manifest # return_list
