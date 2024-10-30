
import string
import random
from datetime import datetime
import logging
import pythonedi

class TestGenerate810(object):

    def get_manifest(self, edi_data):
        manifest = {}
        manifest['edi_data'] = edi_data
        manifest['stats'] = {}
        return manifest

    def test_generate(self):
        self.g = pythonedi.EDIGenerator()
        invoice_number = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(22))
        po_number = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(22))
        #pythonedi.explain("810", "ITD")
        edi_data = self.get_parser_output()
        try:
            manifest = self.get_manifest(edi_data)
            message = self.g.build(manifest)
            #print("------- This is from parsing: ....\n\n" + message)
        except Exception as e:
            print("------- Generating:\n\n" + message)
            logging.exception(e)

    def test_error_handling(self):
        self.g = pythonedi.EDIGenerator()
        invoice_number = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(22))
        po_number = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(22))

        edi_data = {
            "ISA": [
                "00", # Authorization Information Qualifier
                "", # Authorization Information
                "00", # Security Information Qualifier
                "", # Security Information
                "ZZ", # Interchange Sender ID Qualifier
                "306000000", # Interchange Sender ID
                "ZZ", # Interchange Receiver ID Qualifier
                "306009503", # Interchange Receiver ID
                datetime.now(), # Interchange Date
                datetime.now(), # Interchange Time
                "U", # Interchange Control Standards Identifier
                "00401", # Interchange Control Version Number
                "000010770", # Interchange Control Number
                "0", # Acknowledgment Requested
                "P", # Usage Indicator
                "/" # Component Element Separator
            ],
            "TXN": [{
                "ST": [
                    "810",
                    "123456"
                ],
                "BIG": [
                    datetime.now(), # Invoice date
                    invoice_number, # Invoice number
                    datetime.now(), # Purchase order date
                    po_number,
                    None,
                    None,
                    "CN"
                ],
                "REF": [
                    "AP"
                ]
            }]
        }
        old_level = pythonedi.Debug.level
        pythonedi.Debug.level = 0 # Turn off explaining for intentional exceptions

        try:
            manifest = self.get_manifest(edi_data)
            message = self.g.build(manifest)
            assert 'should report error'
        except Exception as e:
            logging.exception(e)

        pythonedi.Debug.level = old_level


    def get_parser_output(self):
        return {
            "ISA": {
                "ISA01": "00",
                "ISA02": "          ",
                "ISA03": "00",
                "ISA04": "          ",
                "ISA05": "ZZ",
                "ISA06": "CMACGM         ",
                "ISA07": "ZZ",
                "ISA08": "HALPORT        ",
                "ISA09": "180514",
                "ISA10": "0743",
                "ISA11": "U",
                "ISA12": "00401",
                "ISA13": 658408998,
                "ISA14": "0",
                "ISA15": "P",
                "ISA16": ">"
            },
            "GS": {
                "GS01": "SO",
                "GS02": "CMACGM",
                "GS03": "A6A",
                "GS04": "20180514",
                "GS05": "0743",
                "GS06": 658408998,
                "GS07": "X",
                "GS08": "004010"
            },
            "TXN": [
                {
                    "ST": {
                        "ST01": "311",
                        "ST02": "658408998"
                    },
                    "B2A": {
                        "B2A01": "0",
                        "B2A02": "24"
                    },
                    "N9": [
                        {
                            "N901": "BI",
                            "N902": "9558"
                        },
                        {
                            "N901": "OB",
                            "N902": "RTM9099592"
                        },
                        {
                            "N901": "AAO",
                            "N902": "9381CE91682071811"
                        },
                        {
                            "N901": "ZZ",
                            "N902": "Y"
                        }
                    ],
                    "V1": {
                        "V101": "",
                        "V102": "MAERSK PALERMO",
                        "V103": "",
                        "V104": "0ED04E1MA"
                    },
                    "V3": {
                        "V301": "NLRTM",
                        "V302": "20180516",
                        "V303": "CAHAL",
                        "V304": "20180602"
                    },
                    "DTM": [
                        {
                            "DTM01": "139",
                            "DTM02": "20180515",
                            "DTM03": "1630"
                        }
                    ],
                    "L_N1": [
                        {
                            "N1": {
                                "N101": "CN",
                                "N102": "BLUE ANCHOR LINE"
                            },
                            "N3": [
                                {
                                    "N301": "77 FOSTER CRESCENT"
                                }
                            ],
                            "N4": {
                                "N401": "MISSISSAUGA",
                                "N402": "ON",
                                "N403": "L5R0K1",
                                "N404": "CA"
                            }
                        },
                        {
                            "N1": {
                                "N101": "SH",
                                "N102": "KUEHNE + NAGEL NV"
                            },
                            "N3": [
                                {
                                    "N301": "LLOYDSTRAAT 35"
                                }
                            ],
                            "N4": {
                                "N401": "ROTTERDAM",
                                "N402": "",
                                "N403": "",
                                "N404": "NL"
                            }
                        },
                        {
                            "N1": {
                                "N101": "NP",
                                "N102": "BLUE ANCHOR LINE"
                            },
                            "N3": [
                                {
                                    "N301": "77 FOSTER CRESCENT"
                                }
                            ],
                            "N4": {
                                "N401": "MISSISSAUGA",
                                "N402": "ON",
                                "N403": "L5R0K1",
                                "N404": "CA"
                            }
                        }
                    ],
                    "R4": [
                        {
                            "R401": "R",
                            "R402": "SC",
                            "R403": "ROTTERDAM",
                            "R404": "ROTTERDAM",
                            "R405": "NL"
                        },
                        {
                            "R401": "3",
                            "R402": "CD",
                            "R403": "0009",
                            "R404": "",
                            "R405": "",
                            "R406": "HALTERM TERMINALS"
                        },
                        {
                            "R401": "4",
                            "R402": "CD",
                            "R403": "0009"
                        },
                        {
                            "R401": "E",
                            "R402": "SC",
                            "R403": "HALIFAX, NS",
                            "R404": "HALIFAX, NS",
                            "R405": "CA"
                        },
                        {
                            "R401": "M",
                            "R402": "CD",
                            "R403": "2036"
                        }
                    ],
                    "L_LX": [
                        {
                            "LX": {
                                "LX01": 1
                            },
                            "Y2": [
                                {
                                    "Y201": "",
                                    "Y202": "",
                                    "Y203": "PP",
                                    "Y204": "45G1"
                                }
                            ],
                            "ED": {
                                "ED01": "TCKU",
                                "ED02": "9200295",
                                "ED03": "L"
                            },
                            "M7": [
                                {
                                    "M701": "100516"
                                }
                            ],
                            "L_L0": [
                                {
                                    "L0": {
                                        "L001": 1,
                                        "L002": "",
                                        "L003": "",
                                        "L004": 4477.01,
                                        "L005": "G",
                                        "L006": "",
                                        "L007": "",
                                        "L008": 11,
                                        "L009": "PCS",
                                        "L010": "",
                                        "L011": "K"
                                    },
                                    "L5": [
                                        {
                                            "L501": 1,
                                            "L502": "FREIGHT COLLECT"
                                        },
                                        {
                                            "L501": 2,
                                            "L502": "FARMING EQUIPMENT"
                                        },
                                        {
                                            "L501": 3,
                                            "L502": "HS-CODE:84361000"
                                        },
                                        {
                                            "L501": 4,
                                            "L502": "NVOCC HOUSE BILL REF NO.8041RTM2235818"
                                        }
                                    ]
                                }
                            ]
                        }
                    ],
                    "SE": {
                        "SE01": 33,
                        "SE02": "658408998"
                    }
                }
            ],
            "GE": {
                "GE01": 1,
                "GE02": 658408998
            },
            "IEA": {
                "IEA01": 1,
                "IEA02": 658408998
            }
        }