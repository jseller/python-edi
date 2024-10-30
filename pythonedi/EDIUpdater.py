
WINDOWS_LINE_ENDING = b'\r\n'
UNIX_LINE_ENDING = b'\n'
MAC_LINE_ENDING = b'\r'

class EdiUpdater(object):

    def __init__(self, manifest, edi_file):
        self.manifest = manifest
        self.edi_file = edi_file
        self.corrected = b''
        self.line_ending = UNIX_LINE_ENDING

    def get_codes(self, transaction_num):
        match_text = b''
        transaction = self.manifest.transactions[transaction_num]
        if len(transaction.commodity_matches) > 0:
            '''
            for match in transaction.commodity_matches:
                match_text += bytes(match.code, 'utf-8')
            # TODO taking first one for now
            '''
            match = transaction.commodity_matches[0]
            match_text += bytes(match.code, 'utf-8')
        return match_text    

    def update(self):
        match_text = b''
        transaction_num = 0
        code_corrected = False
        in_L5 = False
        with open(self.edi_file, 'rb') as open_file:
            for content in open_file:
                if content.endswith(WINDOWS_LINE_ENDING):
                    self.line_ending =  WINDOWS_LINE_ENDING
                elif content.endswith(MAC_LINE_ENDING):
                    self.line_ending = MAC_LINE_ENDING
                if content.startswith(b'ST'):
                    code_corrected = False
                if not code_corrected:
                    codes = self.get_codes(transaction_num)
                    if content.startswith(b'L5*1'):
                        #check for columns
                        parts = content.split(b'*')
                        if len(parts) == 3:
                            parts[2] = parts[2].replace(self.line_ending,b'')
                            parts.append(codes + self.line_ending)
                        if len(parts) == 2:
                            parts.append(b'*')
                            parts.append(codes + self.line_ending)
                        match_text = b'*'.join(parts)
                if match_text:
                    self.corrected += match_text
                    match_text = b''
                    code_corrected = True
                else:
                    self.corrected += content
                if content.startswith(b'SE'):
                    transaction_num += 1
        
    def output(self, file_path):
        with open(file_path, 'wb') as open_file:
            open_file.write(self.corrected)
