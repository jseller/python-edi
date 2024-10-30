"""
Parses a provided dictionary set and tries to build an EDI message from the data.
Provides hints if data is missing, incomplete, or incorrect.
"""

import datetime
import logging
from .supported_formats import supported_formats

class EDIGenerator(object):

    def __init__(self, element_delimiter = '*', segment_delimiter = '\n', data_delimiter = "`"):
        # Set default delimiters
        self.element_delimiter = element_delimiter
        self.segment_delimiter = segment_delimiter
        self.data_delimiter = data_delimiter
        self.correct_output_spacing = False
        self.status = {}
        self.transactions = []
        self.control_number = 0
        self.total_segments = 0
        self.total_errors = 0

    def get_edi_format(self, transactions):
        # Check for transaction set ID in data
        first_transaction = transactions[0].get('ST')
        if not first_transaction:
            raise ValueError("No transaction set header found in data.")
        ts_id = first_transaction.get('ST01')
        if ts_id not in supported_formats:
            raise ValueError("Transaction set type '{}' is not supported. Valid types include: {}".format(
                ts_id,
                "".join(["\n - " + f for f in supported_formats])
            ))
        return supported_formats[ts_id]

    def find_commodity(self, transaction):
        for segment in transaction.get('L_LX'):
            for descriptions in segment.get('L_L0'):
                for lading in descriptions.get('L5'):
                    if lading.get('L501') == 3:
                        return lading.get('L502')
 
    def build(self, manifest):
        """
        Compiles a transaction set (as a dict) into an EDI message
        """
        data = manifest.get('edi_data')
        data_transactions = data.get('TXN')
        if not data_transactions:
            raise ValueError("No transactions found in data")
        edi_format = self.get_edi_format(data_transactions)
        '''
        get the header segments, isa and gs
        get all the transactions
        get the footer segments ga and iea
        '''
        isa_schema = next(item for item in edi_format if item['id'] == 'ISA')
        gs_schema = next(item for item in edi_format if item['id'] == 'GS')
        output = self.build_transaction(data, [isa_schema, gs_schema])      
        txn_schema = [item for item in edi_format if item['id'] not in ['ISA', 'GS', 'GE', 'IEA']]
        reference_number = '_'.join([
                            data['GS']['GS02'], data['GS']['GS03'],
                            data['GS']['GS04'], data['GS']['GS05']
                            ])
        for transaction in data_transactions:
            self.control_number = transaction.get('ST').get('ST02')
            reference_number += '_' + self.control_number
            self.transactions.append(reference_number)
            #set commodity code if corrections
            self.transaction_commodity = self.find_commodity(transaction) 
            output.extend(self.build_transaction(transaction, txn_schema))
            if manifest.get('transactions'):
                for transaction in manifest.get('transactions'):
                    if transaction.get('control_number') == self.control_number:
                        transaction['status'] = self.status.get(self.control_number)
        ge_schema = next(item for item in edi_format if item['id'] == 'GE')
        iea_schema = next(item for item in edi_format if item['id'] == 'IEA')
        output.extend(self.build_transaction(data, [ge_schema, iea_schema]))
        out_file = self.segment_delimiter.join(output) + self.segment_delimiter
        manifest['out_file'] = out_file
        return manifest
  
    def build_transaction(self, data, edi_format):
        output_segments = []
        # Walk through the format definition to compile the output message
        for section in edi_format:
            if section["type"] == "segment":
                if section["id"] not in data:
                    if section["req"] == "O":
                        # Optional segment is missing - that's fine, keep going
                        continue
                    elif section["req"] == "M":
                        # Mandatory segment is missing - explain it and then fail
                        raise ValueError("EDI data is missing mandatory segment '{}'.".format(section["id"]))
                    else:
                        raise ValueError("Unknown 'req' value '{}' when processing format for segment '{}' in set '{}'".format(section["req"], section["id"], ts_id))
                segment_data = data[section["id"]]
                if isinstance(segment_data, list):
                    for segment_element in segment_data:
                        output_segments.append(self.build_segment(section, segment_element))
                else:        
                    output_segments.append(self.build_segment(section, segment_data))
            elif section["type"] == "loop":
                if section["id"] not in data:
                    mandatory = [segment for segment in section["segments"] if segment["req"] == "M"]
                    if len(mandatory) > 0:
                        raise ValueError("EDI data is missing loop {} with mandatory segment(s) {}".format(section["id"], ", ".join([segment["id"] for segment in mandatory])))
                    else:
                        # No mandatory segments in loop - continue
                        continue
                # Verify loop length
                if len(section["segments"]) > section["repeat"]:
                    raise ValueError("Loop '{}' has {} segments (max {})".format(section["id"], len(section["segments"]), section["repeat"]))
                # Iterate through and build segments in loop
                for iteration in data[section["id"]]:
                    for segment in section["segments"]:
                        if segment["id"] not in iteration:
                            if segment["req"] == "O":
                                # Optional segment is missing - that's fine, keep going
                                continue
                            elif segment["req"] == "M":
                                # Mandatory segment is missing - explain loop and then fail
                                raise ValueError("EDI data in loop '{}' is missing mandatory segment '{}'.".format(section["id"], segment["id"]))
                            else:
                                raise ValueError("Unknown 'req' value '{}' when processing format for segment '{}' in set '{}'".format(segment["req"], segment["id"], ts_id))                    
                        segment_data = iteration[segment["id"]]
                        if segment['type'] == 'loop':
                            segment_sections = segment.get('segments')
                            for segment_element in segment_data:    
                                for elem in segment_element:
                                    elem_data = segment_element[elem]
                                    loop_schema = next(item for item in segment_sections if item['id'] == elem)
                                    if isinstance(elem_data, list):
                                        for elem_d in elem_data:
                                            output_segments.append(self.build_segment(loop_schema, elem_d))
                                    else:
                                        output_segments.append(self.build_segment(loop_schema, elem_data))  
                        elif isinstance(segment_data, list):
                            for segment_element in segment_data:
                                output_segments.append(self.build_segment(segment, segment_element))
                        else:
                            output_segments.append(self.build_segment(segment, segment_data))

        return output_segments

    def build_segment(self, segment, segment_data):
        # Parse segment elements
        if segment_data.get('L501') == 3:
            #data field should have commodity code
            commodity = segment_data.get('L502')
            # get found commodity
            if not commodity:
                segment_data['L502'] = self.transaction_commodity

        #print("\nBTS "+str(segment) +"\n BData: "+str(segment_data) +" \n\n")
        output_elements = [segment["id"]]
        for e_data, e_format in zip(segment_data.values(), segment["elements"]):
            output_elements.append(self.build_element(e_format, e_data))
        
        # End of segment. If segment has syntax rules, validate them.
        if "syntax" in segment:
            for rule in segment["syntax"]:
                # Note that the criteria indexes are one-based 
                # rather than zero-based. However, the output_elements
                # array is prepopulated with the segment name,
                # so the net offset works perfectly!
                if rule["rule"] == "ATLEASTONE": # At least one of the elements in `criteria` must be present
                    found = False
                    for idx in rule["criteria"]:
                        if idx >= len(output_elements):
                            break
                        elif output_elements[idx] != "":
                            found = True
                    if found is False:
                        # None of the elements were found
                        required_elements = ", ".join(["{}{:02d}".format(segment["id"], e) for e in rule["criteria"]])
                        raise ValueError("Syntax error parsing segment {}: At least one of {} is required.".format(segment["id"], required_elements))
                elif rule["rule"] == "ALLORNONE": # Either all the elements in `criteria` must be present, or none of them may be
                    found = 0
                    for idx in rule["criteria"]:
                        if idx >= len(output_elements):
                            break
                        elif output_elements[idx] != "":
                            found += 1
                    if 0 < found < len(rule["criteria"]):
                        # Some but not all the elements are present
                        required_elements = ", ".join(["{}{:02d}".format(segment["id"], e) for e in rule["criteria"]])
                        raise ValueError("Syntax error parsing segment {}: If one of {} is present, all are required.".format(segment["id"], required_elements))
                elif rule["rule"] == "IFATLEASTONE": # If the first element in `criteria` is present, at least one of the others must be
                    found = 0
                    # Check if first element exists and is set
                    if rule["criteria"][0] < len(output_elements) and output_elements[rule["criteria"][0]] != "":
                        for idx in rule["criteria"][1:]:
                            if idx >= len(output_elements):
                                break
                            elif output_elements[idx] != "":
                                found += 1
                        if 0 < found < len(rule["criteria"]):
                            # Some but not all the elements are present
                            first_element = "{}{:02d}".format(segment["id"], rule["criteria"][0])
                            required_elements = ", ".join(["{}{:02d}".format(segment["id"], e) for e in rule["criteria"][0]])
                            raise ValueError("Syntax error parsing segment {}: If {} is present, at least one of {} are required.".format(segment["id"], first_element, required_elements))
            
        return self.element_delimiter.join(output_elements)

    def validate_element(self, e_format, text):
        minlen = e_format["length"]["min"]
        maxlen = e_format["length"]["max"]
        status = 'passed'
        message = 'valid'
        value = text
        if e_format["req"] == 'M' and len(value) == 0:
            message = ' is required.'
            status = 'failed'
            self.total_errors += 1
        else:
            if e_format["req"] == 'M' and len(value) < int(minlen):
                message = ' minimum: '+str(minlen)+' maximum: '+str(maxlen)
                status = 'failed'
                self.total_errors += 1
            elif e_format["req"] == 'M' and len(value) > int(maxlen):
                message = ' maximum: '+str(minlen)+' maximum: '+str(maxlen)
                status = 'failed'
                self.total_errors += 1
        self.total_segments += 1
        elem_id = e_format['id']
        result = {'status': status, 'control_number': str(self.control_number), 'element': elem_id, 'segment': e_format, 'message': message, 'value':text}
        #print("checking element len:%d min:%d max:%d (%s) %s\n"  % (len(text), minlen, maxlen, text, message ))
        if not self.status.get(self.control_number):
            self.status[self.control_number] = []
        self.status[self.control_number].append(result)

    def build_element(self, e_format, e_data):
        element_id = e_format["id"]
        formatted_element = ""
        if e_data is None:
            if e_format["req"] == "M":
                raise ValueError("Element {} ({}) is mandatory".format(element_id, e_format["name"]))
            elif e_format["req"] == "O":
                return ""
            else:
                raise ValueError("Unknown 'req' value '{}' when processing format for element '{}' in set '{}'".format(e_format["req"], element_id, ts_id))
        try:
            if e_format["data_type"] == "AN":
                formatted_element = e_data
                self.validate_element(e_format, e_data)
            elif e_format["data_type"] == "DT":
                try:
                    if len(e_data) == 8:
                        value = datetime.datetime.strptime(e_data, "%Y%m%d")
                    elif len(e_data) == 6:
                        value = datetime.datetime.strptime(e_data, "%y%m%d")
                except Exception as e:
                    raise ValueError("Invalid length ({}) for date field in element '{}' in set '{}'".format(e_format["length"], element_id, ts_id))
                formatted_element = e_data
            elif e_format["data_type"] == "TM":
                try:
                    if len(e_data) == 4:
                        value = datetime.datetime.strptime(e_data, "%H%M")
                    elif len(e_data) == 6:
                        value = datetime.datetime.strptime(e_data, "%H%M%S")
                except Exception as e:
                    raise ValueError("Invalid length ({}) for time field in element '{}' in set '{}'".format(e_format["length"], element_id, ts_id))    
                formatted_element = e_data
            elif e_format["data_type"].startswith("R"):
                # check for float? R8 mystery
                if e_data:
                    if e_data > int(e_data):
                        formatted_element = str(e_data)
                    else:
                        formatted_element = str(int(e_data))    
            elif e_format["data_type"].startswith("N"):
                self.validate_element(e_format, str(e_data))
                if e_data:
                    formatted_element = "{:0{length}.{decimal}f}".format(float(e_data), length=e_format["length"]["min"], decimal=e_format["data_type"][1:])
            elif e_format["data_type"] == "ID":
                formatted_element = str(e_data)
                if not e_format["data_type_ids"]:
                    #Debug.log_warning("No valid IDs provided for element '{}'. Allowing anyway.".format(e_format["name"]))
                    pass
                elif e_data not in e_format["data_type_ids"]:
                    #Debug.log_warning("ID '{}' not recognized for element '{}'. Allowing anyway.".format(e_data, e_format["name"]))
                    pass
                self.validate_element(e_format, e_data)
            elif e_format["data_type"] == "":
                if element_id == "ISA16":
                    # Component Element Separator
                    self.data_delimiter = str(e_data)[0]
                    formatted_element = str(e_data)
                else:
                    raise ValueError("Undefined behavior for empty data type with element '{}'".format(element_id))
        except:
            raise ValueError("Error converting '{}' to data type '{}'".format(e_data, e_format["data_type"]))

        # Pad/trim formatted element to fit the field min/max length respectively
        if self.correct_output_spacing:
            formatted_element += " "*(e_format["length"]["min"]-len(formatted_element))
            formatted_element = formatted_element[:e_format["length"]["max"]]

        # Add element to list
        return formatted_element
