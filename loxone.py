# -*- coding: utf-8 -*-
import logging
import requests
from xml.etree import ElementTree
import pprint
import json
import tempfile
import re
from kalliope.core.NeuronModule import NeuronModule
from kalliope.core.NeuronModule import MissingParameterException, InvalidParameterException

logging.basicConfig()
logger = logging.getLogger("kalliope")

#HOST = "127.0.0.1"
#Path definition
STRUCTUREDEF = "/data/Loxapp3.json"
VERSION = "/dev/sps/LoxAPPversion"
SPSIO = "/dev/sps/io/"
#USER = "UserName"
#PASSWORD = "NOPASSWORD"

# Control elements used in Loxone
TYPE_SWITCH = ["TimedSwitch", "Switch"]
TYPE_LIGHTCONTROL = ["LightController"]
TYPE_JALOUSIE = ["Jalousie"]

# Categories used in Loxone
CAT_LIGTH = "lights"
CAT_JALOUSIE = "shading"
CAT_UNDEF = "undefined"


class Loxone(NeuronModule):

    def __init__(self, *args, **kwargs):
        # call super init
        super(Loxone, self).__init__(*args, **kwargs)

        # get parameters from the neuron
        self._host = kwargs.get('loxone_ip', None)
        self._user = kwargs.get('loxone_user', None)
        self._password = kwargs.get('loxone_password', None)
        
        self.change_room = kwargs.get('control_room', None)
        self.change_type = kwargs.get('control_type', None) 
        self.change_name = kwargs.get('control_name', None)         
        self.change_newstate = kwargs.get('newstate', None) 
        
        # define request headers
        self._headers = {'accept': 'application/json'}

        # check if parameters have been provided
        if self._is_parameters_ok():            

            # check provided args and do that
            if self.change_name is not None:
                self.change_switch_state_byname(self.change_name, self.change_newstate)
            

    def _is_parameters_ok(self):       
        """
        Check if received parameters are ok to perform operations in the neuron
        
        :return: true if parameters are ok, raise an exception otherwise
        .. raises:: InvalidParameterException
        """
        # host ip is set
        if self._host is None:
            raise MissingParameterException("Loxone neuron needs a miniserver IP")

        # host user is set
        if self._user is None:
            raise MissingParameterException("Loxone neuron needs a miniserver user")

        # host password is set
        if self._password is None:
            raise MissingParameterException("Loxone neuron needs a miniserver user password")
        
        # load loxone config from miniserver
        if not self.load_config():
            raise MissingParameterException("Loxone neuron can't load miniserver structure definition")
    
        return True

    def change_switch_state_byuuid(self, controluuid,  newstate):
        """
        Changes the state of a switch identified by controlname

        :param controluuid: uuid of the control element
        :param newstate: new state of the switch
        :return: True if successful, False if not
        """ 
        r = requests.get("http://"+self._host + SPSIO+controluuid+"/"+newstate,
                                    auth=(self._user, self._password))    
        try:
            r.raise_for_status()       
        except requests.exceptions.HTTPError:
            logger.critical('Change switch State failed with response: %r',
                                  r.text,
                                  exc_info=True)
            return False
        except requests.exceptions.RequestException:
            logger.critical('Change switch State failed.', exc_info=True)
            return False
            
 #TODO: [Feature] check if state is correct -> analyse JSON answer           
        return True 

    def change_switch_state_byname(self, controlname,  newstate):
        """
        Changes the state of a switch identified by controlname

        :param controlname: name of the switch
        :param newstate: new state of the switch
        :return: True if successful, False if not        
        """
        if self.get_uuid_by_name(controlname) is not None:
            return self.change_switch_state_byuuid(self.get_uuid_by_name(controlname), newstate)
        else: 
            return False
        
    def get_uuid_by_name(self, controlname):
        """
        Returns UUID identified by controlname

        :param controlname: name of the switch
        :return: UUID of control in the structure definition or None if not found
        """
        for controlgroup in self._controls:            
            subcontrol=self._controls[controlgroup]["controls"]
            for element in subcontrol:
                if subcontrol[element]["name"] == controlname:
                    return subcontrol[element]["uidAction"]
        return None            

    def load_config(self):
        """
        Loads the JSON Config File (Structure Definition) of the loxone miniserver
        
        :return: true if config is loaded and parsed, false otherwise
        """
        # load structure definition
#TODO: [Feature] config should be cached and only loaded when needed -> check VERSION!          
        r = requests.get("http://"+self._host + STRUCTUREDEF, auth=(self._user, self._password))
        try:
            r.raise_for_status()
            raw_info = r.json()['msInfo']
            raw_rooms = r.json()['rooms']
            raw_controls = r.json()['controls']
            raw_cats = r.json()['cats']
        except requests.exceptions.HTTPError:
            logger.critical('Structure Definition Request failed with response: %r',
                                  r.text,
                                  exc_info=True)
            return False
        except requests.exceptions.RequestException:
            logger.critical('Structure Definition Request failed.', exc_info=True)
            return False
        except ValueError as e:
            logger.critical('Structure Definition cannot be parsed, response: %s',
                                  e.args[0])
            return False
        except KeyError:
            logger.critical('Structure Definition cannot be parsed. KeyError.',
                                  exc_info=True)
            return False

        # Parse structure
        try:
            # Get Info
            self._language=raw_info['languageCode']
            self._location=raw_info['location']
            self._roomtitle=raw_info['roomTitle']

            # Get rooms
            self._rooms={}            
            for room in raw_rooms:
                self._rooms[room]={"name":raw_rooms[room]['name'],"uid":raw_rooms[room]['uuid']}

            # Get categories
            self._controls={}            
            for cat in raw_cats: 
                self._controls[cat]={"name":raw_cats[cat]['name'],"uid":raw_cats[cat]['uuid'],"type":raw_cats[cat]['type'],"controls":{}}

            # fill controls
            self.extract_controls(raw_controls)    

        except KeyError:
            self._logger.critical('Structure Definition cannot be parse. KeyError.',
                                  exc_info=True)
            return False
#TODO: FIX Language check
        # Check Language
        #try:
        #    language = self.profile['language']
        #except KeyError:
        #    language = 'en-US'
        #if language.split('-')[1]==self._language:
        #    raise ValueError("Home automation language is %s. But your profile language is set to %s",self._language,language)

        # debug print
        pprint.pprint(self._controls)

        pprint.pprint(self._rooms)
        
        return True

    def extract_controls(self, jsonconfig):
        """
        Parse the given JSON and extract the control information
        
        :param jsonconfig: controls block of the json file
        """              
        # Step though each entry
        for control in jsonconfig:
                if jsonconfig[control]['type'] in TYPE_SWITCH:
                    self._controls[jsonconfig[control]['cat']]['controls'][control]={ \
                        "name":jsonconfig[control]['name'], \
                        "uidAction":jsonconfig[control]['uuidAction'],\
                        "room":jsonconfig[control]['room'],\
                        "type":jsonconfig[control]['type']}
                elif jsonconfig[control]['type'] in TYPE_LIGHTCONTROL:
                        subcontrols=jsonconfig[control]['subControls']
                        for subcontrol in subcontrols:
                            if subcontrols[subcontrol]['type'] == "Switch":
                                self._controls[jsonconfig[control]['cat']]['controls'][subcontrol]={ \
                                "name":subcontrols[subcontrol]['name'], \
                                "uidAction":subcontrols[subcontrol]['uuidAction'],\
                                "room":jsonconfig[control]['room'],\
                                "type":subcontrols[subcontrol]['type']}
                elif jsonconfig[control]['type'] in TYPE_JALOUSIE:
                    self._controls[jsonconfig[control]['cat']]['controls'][control]={ \
                        "name":jsonconfig[control]['name'], \
                        "uidAction":jsonconfig[control]['uuidAction'],\
                        "room":jsonconfig[control]['room'],\
                        "type":jsonconfig[control]['type']}     
      
                # IRoomController
                # InfoOnlyAnalog
        return
