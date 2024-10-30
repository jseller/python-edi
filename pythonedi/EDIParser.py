"""
Parses a provided EDI message and tries to build a dictionary from the data
Provides hints if data is missing, incomplete, or incorrect.
"""

import datetime
import logging

from .supported_formats import supported_formats

WINDOWS_LINE_ENDING = '\r\n'
UNIX_LINE_ENDING = '\n'
MAC_LINE_ENDING = '\r'

class EDIParser(object):

    def __init__(self, source):
        #source, carrier
        self.source = source
        self.segment_delimiter = UNIX_LINE_ENDING
        self.stats = {}
        self.stats['source'] = self.source

    def detect(self, data):
        self.element_delimiter = data[3:4]
        last_four = bytes(data[-4:], 'utf-8')
        print('last '+str(last_four))
        if last_four.endswith(bytes(WINDOWS_LINE_ENDING, 'utf-8')):
            self.segment_delimiter = str(WINDOWS_LINE_ENDING)
        elif last_four.endswith(bytes(MAC_LINE_ENDING, 'utf-8')):
            self.segment_delimiter = MAC_LINE_ENDING
        elif last_four.endswith(bytes('~', 'utf-8')):
            self.segment_delimiter = '~'
        # Set EDI format to use
        index = 'ST'+self.element_delimiter
        find_index = data.find(index)
        found_edi_format = data[find_index+ 3:find_index + 6]
        if found_edi_format in supported_formats:
            self.edi_format = supported_formats[found_edi_format]
        self.stats['segment_delimiter'] = self.segment_delimiter
        self.stats['element_delimiter'] = self.element_delimiter
        self.stats['edi_format'] = found_edi_format

    def parse(self, data):
        self.detect(data)
        edi_segments = data.split(self.segment_delimiter)
        if self.edi_format is None:
            raise NotImplementedError("EDI format autodetection not built yet. Please specify an EDI format.")

        manifest = {}
        in_transaction = False
        transactions = []
        transaction_count = 0
        transaction_segments = {}

        while len(edi_segments) > 0:
            segment = edi_segments[0]
            if segment == "":
                edi_segments = edi_segments[1:]
                continue # Line is blank, skip
            # Capture current segment name
            segment_name = segment.split(self.element_delimiter)[0]
            segment_obj = None
            # Find corresponding segment/loop format
            for seg_format in self.edi_format:
                # Check if segment is just a segment, a repeating segment, or part of a loop
                if seg_format["id"] == segment_name and seg_format["max_uses"] == 1:
                    # Found a segment
                    segment_obj = self.parse_segment(segment, seg_format)
                    edi_segments = edi_segments[1:]
                    break
                elif seg_format["id"] == segment_name and seg_format["max_uses"] > 1:
                    # Found a repeating segment
                    segment_obj, edi_segments = self.parse_repeating_segment(edi_segments, seg_format)
                    break
                elif seg_format["id"] == "L_" + segment_name:
                    # Found a loop
                    segment_name = seg_format["id"]
                    segment_obj, edi_segments = self.parse_loop(edi_segments, seg_format)
                    break
                
            if segment_obj is None:
                logging.error("Unrecognized segment: {}".format(segment))
                edi_segments = edi_segments[1:] # Skipping segment
                continue
                # raise ValueError
            
            #handle multiple transactions in same manifest
            if segment_name == 'ST':
                in_transaction = True
            if in_transaction:
                transaction_segments[segment_name] = segment_obj
            else:
                if segment_name == 'GE':
                    manifest['TXN'] = transactions
                manifest[segment_name] = segment_obj                
            if segment_name == 'SE':
                transactions.append(transaction_segments)
                transaction_segments = {}
                in_transaction = False

        return self.stats, manifest

    def parse_segment(self, segment, segment_format):
        """ Parse a segment into a dict according to field IDs """
        fields = segment.split(self.element_delimiter)
        if fields[0] != segment_format["id"]:
            raise TypeError("Segment type {} does not match provided segment format {}".format(fields[0], segment_format["id"]))
        elif len(fields)-1 > len(segment_format["elements"]):
            logging.info(segment_format)
            raise TypeError("Segment has more elements than segment definition")

        to_return = {}
        for field, element in zip(fields[1:], segment_format["elements"]): # Skip the segment name field
            key = element["id"]
            if element["data_type"] == "DT":
                value = field
            elif element["data_type"] == "TM":
                value = field
            elif element["data_type"] == "N0" and field != "":
                value = int(field)
            elif element["data_type"].startswith("N") and field != "":
                value = float(field) / (10**int(element["data_type"][-1]))
            elif element["data_type"] == "R" and field != "":
                value = float(field)
            else:
                value = field
            to_return[key] = value

        return to_return


    def parse_repeating_segment(self, edi_segments, segment_format):
        """ Parse all instances of this segment, and return any remaining segments with the seg_list """
        seg_list = []

        while len(edi_segments) > 0:
            segment = edi_segments[0]
            segment_name = segment.split(self.element_delimiter)[0]
            if segment_name != segment_format["id"]:
                break
            seg_list.append(self.parse_segment(segment, segment_format))
            edi_segments = edi_segments[1:]

        return seg_list, edi_segments

    def parse_loop(self, edi_segments, loop_format):
        """ Parse all segments that are part of this loop, and return any remaining segments with the loop_list """
        loop_list = []
        loop_dict = {}

        while len(edi_segments) > 0:
            segment = edi_segments[0]
            segment_name = segment.split(self.element_delimiter)[0]
            segment_obj = None

            # Find corresponding segment/loop format
            for seg_format in loop_format["segments"]:
                # Check if segment is just a segment, a repeating segment, or part of a loop
                if seg_format["id"] == segment_name and seg_format["max_uses"] == 1:
                    # Found a segment
                    segment_obj = self.parse_segment(segment, seg_format)
                    edi_segments = edi_segments[1:]
                elif seg_format["id"] == segment_name and seg_format["max_uses"] > 1:
                    # Found a repeating segment
                    segment_obj, edi_segments = self.parse_repeating_segment(edi_segments, seg_format)
                elif seg_format["id"] == "L_" + segment_name:
                    # Found a loop
                    segment_name = seg_format["id"]
                    segment_obj, edi_segments = self.parse_loop(edi_segments, seg_format)
            #print(segment_name, segment_obj)
            if segment_obj is None:
                # Reached the end of valid segments; return what we have
                break
            elif segment_name == loop_format["segments"][0]["id"] and loop_dict != {}: 
                # Beginning a new loop, tie off this one and start fresh
                loop_list.append(loop_dict.copy())
                loop_dict = {}
            loop_dict[segment_name] = segment_obj
        if loop_dict != {}:
            loop_list.append(loop_dict.copy())
        return loop_list, edi_segments
