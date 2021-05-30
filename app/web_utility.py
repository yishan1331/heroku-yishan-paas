# -*- coding: utf-8 -*-
#!/usr/bin/env python2.7
#web_utility module description
"""
==============================================================================
created: 

Last update: 
 
Developer: Wei-Chun Chang 
 
Lite Version 1 @Yishan08032019
 
Filename: web_utility.py
 
==============================================================================
"""

#=======================================================
#system level modules
#=======================================================
import os, sys, inspect
import time, datetime
import logging
import ConfigParser

#=======================================================
#user-defined modules
#=======================================================
import authentic_utility

FORMAT = '[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s'

# {{{ def get_input_value(inputdata, attribute, logpath):
def get_input_value(inputdata, attribute, system):
    '''
    @summary: given list and attribute, return value
    '''

    #logging.basicConfig(filename=logpath, format=FORMAT, level=logging.INFO)

    if attribute in inputdata:
        if inputdata[attribute] == "":
            return False
        return inputdata[attribute]
    else:
        #logging.error('[cannot find %s]' % attribute)
        return False
# }}}

# {{{ def get_json_value(jsondata, attribute, logpath):
def get_json_value(jsondata, attribute, logpath):
    '''
    @summary: given json data and attribute, return value
    '''

    logging.basicConfig(filename=logpath, format=FORMAT, level=logging.INFO)
    if attribute in jsondata:
        return jsondata[attribute]
    else:
        logging.error('[cannot find %s]' % attribute)
        return False
# }}}

# {{{ def check_parameters(data, attributes, logpath):
def check_parameters(data, attributes, system):
    '''
    @summary: check data parameters
    '''

    for att in attributes:
        if att not in data:
            return False,att
        else:
            ret = get_input_value(data, att, system)
            if ret == False:
                return ret,att

    return True,None
# }}}

# {{{ def check_json_data(jsondata, attributes, logpath):
def check_json_data(jsondata, attributes, logpath):
    '''
    @summary: check json data
    '''

    for att in attributes:
        value = str(get_json_value(jsondata, att, logpath))
        if value == 'False' or value == '':
            return False

    return True
# }}}

# {{{ def check_signature(ori_signature, string_to_signature, key_loc, logpath):
def check_signature(ori_signature, string_to_signature, key_loc, logpath):
    '''
    @summary: check signature
    '''

    #logging.basicConfig(filename=logpath, format=FORMAT, level=logging.INFO)
    cal_signature = authentic_utility.calculate_signature(key_loc, \
                                                        string_to_signature, \
                                                        logpath)

    if cal_signature == ori_signature:
        return True, cal_signature
    else:
        return False, cal_signature
# }}}

# {{{ def exception_report(err, logpath):
def exception_report(err, logpath):
    #import logging
    #logging.getLogger('fappYott').error(err)
    return True
# }}}

# {{{ def error_report(msg, logpath):
def error_report(msg, logpath):
    logging.basicConfig(filename=logpath, format=FORMAT, level=logging.INFO)
    logging.error(msg)
    return True
# }}}

# {{{ def note_report(msg, logpath):
def note_report(msg, logpath):
    logging.info(msg)
    return True
# }}}
