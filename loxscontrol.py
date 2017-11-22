# -*- coding: utf-8 -*-
"""NeuronModule Class for controlling a Loxone Homeautomation."""

import logging
import requests
from xml.etree import ElementTree
import pprint
import json
import tempfile
import re
from kalliope.core.NeuronModule import NeuronModule
from kalliope.core.NeuronModule import MissingParameterException, \
    InvalidParameterException

logging.basicConfig()
logger = logging.getLogger("kalliope")
#logger.setLevel(logging.DEBUG)


class Loxscontrol(NeuronModule):

    """NeuronModule Class for controlling a Loxone Homeautomation."""

    # Path definition
    STRUCTUREDEF = "/data/Loxapp3.json"
    VERSION = "/dev/sps/LoxAPPversion"
    SPSIO = "/dev/sps/io/"

    # Control elements used in Loxone
    TYPE_SWITCH = ["TimedSwitch", "Switch"]
    TYPE_LIGHTCONTROL = ["LightController"]
    TYPE_JALOUSIE = ["Jalousie"]

    # Categories used in Loxone
    CAT_LIGTH = "lights"
    CAT_JALOUSIE = "shading"
    CAT_UNDEF = "undefined"
    CAT_ROOM = "room"

    # Actions used
    ACT_CHANGE = "change"         #changes a state of an element
    ACT_LIST = "list"                   #names all given elements element

    # Status Code Definitions
    # IncompleteRequest - Parameter is missing or not complete / consistent
    # Complete                 - Completed
    # StateChangeError  -  State of Control Element was not changed.
    #                                   Name not found, or changing failed
    # List                          - List what is given in summary.
    STATUS_CODE_DEF = {
                       "IncompleteRequest",
                       "Complete",
                       "StateChangeError", 
                       "List", 
                       "Error"
                       }

    def __init__(self, *args, **kwargs):
        """class init."""

        # call super init
        super(Loxscontrol, self).__init__(*args, **kwargs)

        # get parameters from the neuron
        self._host = kwargs.get('lx_ip', None)
        self._user = kwargs.get('lx_user', None)
        self._password = kwargs.get('lx_password', None)
        self._controls = kwargs.get('lx_structuredef', None)

        self.action= kwargs.get('action', None)
        self.change_room = kwargs.get('control_room', None)
        self.change_cattype = kwargs.get('control_type', None)
        self.change_name = kwargs.get('control_name', None)
        self.change_newstate = kwargs.get('newstate', None)

        # define request headers
        self._headers = {'accept': 'application/json'}

        # define output
        self.status_code = None
        self.summary = None

        # check if parameters have been provided
        if self._is_parameters_ok():

            # action change
            if self.action == self.ACT_CHANGE:
                self.action_change()

            # action list
            if self.action == self.ACT_LIST:
                self.action_list()
                
            # no valid combination found
            if self.status_code is None:
                MissingParameterException(self.neuron_name +
                                          " needs more information to " +
                                          "process request.")
                self.status_code = "IncompleteRequest"

        else:
            self.status_code = "IncompleteRequest"

        # Finally say what I have done -> use a template
        self.message = {
            "status_code": self.status_code,
            "control_name": self.change_name,
            "control_newstate": self.change_newstate,
            "control_room": self.change_room,
            "summary": self.summary, 
        }
        self.say(self.message)

    def _is_parameters_ok(self):
        """
        Check if received parameters are ok to perform operations.

        :return: true if parameters are ok, raise an exception otherwise
        .. raises:: InvalidParameterException

        """
        # host ip is set
        if self._host is None:
            raise MissingParameterException(self.neuron_name +
                                            ": needs a miniserver IP")

        # host user is set
        if self._user is None:
            raise MissingParameterException(self.neuron_name +
                                            ": needs a miniserver user")

        # host password is set
        if self._password is None:
            raise MissingParameterException(
                self.neuron_name + ": needs a miniserver user " +
                "password"
                )

        # action is set
        if self.action is None:
            raise MissingParameterException(
                self.neuron_name + ": needs an action ")

        # load loxone config from miniserver
        if self._controls is None:
            if not self.load_config():
                raise MissingParameterException(
                    self.neuron_name + ": can't load miniserver structure "
                    "definition"
                    )
            self.show_configinfo()

        # enough information that I can do something?
        if (self.change_name is None) and (self.change_room is None) \
                and (self.change_cattype is None):
            raise MissingParameterException(self.neuron_name +
                                            ": needs something to do")

        return True

    def action_change(self):
        """
        Change the state of a switch 

        """
        
        # name and state is given
        # don't pay attention to categorie
        if (self.change_name is not None) and \
                    (self.change_newstate is not None):
                if self.change_switch_state_byname(self.change_name,
                                                   self.change_newstate):
                    logger.debug(self.neuron_name +
                                 ": State of %s changed to %s",
                                 self.change_name,
                                 self.change_newstate)
                    self.status_code = "Complete"
                else:
                    logger.debug(self.neuron_name +
                                 " State of %s not changed!",
                                 self.change_name)
                    self.status_code = "StateChangeError"

        # Type lights and room and state is given
        if (self.change_cattype == self.CAT_LIGTH) and \
                    (self.change_room is not None) and \
                    (self.change_newstate is not None):
#                if self.change_lights_byroom(self.change_room,
#                                                   self.change_newstate):
#                    logger.debug(self.neuron_name +
#                                 ": State of %s in room %s changed to %s",
#                                 self.change_name,
#                                self.change_newstate)
#                    self.status_code = "Complete"
#                else:
                    logger.debug(self.neuron_name +
                                 " State of %s not changed!",
                                 self.change_name)
                    self.status_code = "StateChangeError"

    def action_list(self):
        """
        List known elements 

        """
        # check that cattype is given
        if (self.change_cattype is not None):
            
                #check cattyp - equals room:
                if (self.change_cattype == self.CAT_ROOM):
                        self.summary=self.list_rooms()
                        if  self.summary is not None:
                            self.status_code = "List"
                        else:
                            self.status_code = "Error"

        # similar for switch, lights etc.



    def change_state_byuuid(self, controluuid,  newstate):
        """
        Change the state of a switch identified by controlname.

        :param controluuid: uuid of the control element
        :param newstate: new state of the switch
        :return: True if successful, False if not

        """

        logger.debug(self.neuron_name +
                     ": Called Change State with %s UID and %s newstate",
                     controluuid,  newstate)
        print controluuid

        try:
            r = requests.get("http://"+self._host + self.SPSIO +
                             controluuid+"/"+newstate,
                             auth=(self._user, self._password))
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            logger.debug(self.neuron_name +
                         ": Change switch state failed with response: %r",
                         r.text)
            return False
        except requests.exceptions.RequestException:
            logger.debug(self.neuron_name+": Change switch state failed.")
            return False

        logger.debug(self.neuron_name +
                     ': UID %s changed state to %s', controluuid, newstate)
# TODO: [Feature] check if state is correct -> analyse JSON answer
        return True

    def change_switch_state_byname(self, controlname,  newstate):
        """
        Change the state of a switch identified by controlname.

        :param controlname: name of the switch
        :param newstate: new state of the switch
        :return: True if successful, False if not

        """
        uuid = self.get_controluuid_by_name(controlname)
        if uuid is not None:
            if self.get_type_by_uuid(uuid) in self.TYPE_SWITCH:
                return self.change_state_byuuid(uuid, newstate)
            else:
                logger.debug(self.neuron_name +
                         ': Name %s is not a Switch', controlname)
                return False
        else:
            logger.debug(self.neuron_name +
                         ': Name %s not found in StructureDef', controlname)
            return False

    def get_type_by_uuid(self,  uuid):
        """
        Return type identified by uuid.

        :param uuid: uuid of the control element
        :return: type of the control element
        or None if not found

        """
        # check categories first
        if uuid in self._controls:
            return self._controls[uuid]['type']
        
        # check controls
        for controlgroup in self._controls:
            subcontrol = self._controls[controlgroup]["controls"]
            if uuid in subcontrol:
                return subcontrol[uuid]["type"]

        # check rooms
        if uuid in self._rooms:
            return self.CAT_ROOM
        return None 
  
    def get_name_by_uuid(self,  uuid):
        """
        Return name identified by uuid.

        :param uuid: uuid of the control element
        :return: name of the control element
        or None if not found

        """
        # check categories first
        if uuid in self._controls:
            return self._controls[uuid]['name']
        
        # check controls
        for controlgroup in self._controls:
            subcontrol = self._controls[controlgroup]["controls"]
            if uuid in subcontrol:
                return subcontrol[uuid]["name"]

        # check rooms
        if uuid in self._rooms:
            return self._rooms[uuid]['name']
        return None   

    def get_controluuid_by_name(self, controlname):
        """
        Return UUID identified by controlname.

        :param controlname: name of the switch
        :return: UUID of control in the structure definition
        or None if not found

        """
        for controlgroup in self._controls:
            subcontrol = self._controls[controlgroup]["controls"]
            for element in subcontrol:
                if subcontrol[element]["name"] in controlname:
                    return subcontrol[element]["uidAction"]
        return None
        
    def list_rooms(self):
        """
        Returns a str of all rooms separated by comma

        """     
        
        roomlist = None

        for room in self._rooms:
            logger.debug(self.neuron_name + ":       %s",self._rooms[room]['name'])
            if roomlist is None:
                roomlist = "%s"%self._rooms[room]['name']
            else:
                roomlist = roomlist + ", %s"%self._rooms[room]['name']
        
        return roomlist    
        

    def show_configinfo(self):
        """
        Print informations about the config to debug output

        """
        
        # General infos
        logger.debug(self.neuron_name + ": Loxone Structure Definition:")
        logger.debug(self.neuron_name + ": Location: %s", self._location)
        logger.debug(self.neuron_name + ": Language: %s", self._language)
        
        # Rooms
        # logger.debug(self.neuron_name + ": Room title: %s", self._roomtitle)        
        logger.debug(self.neuron_name + ": No. of Rooms: %d", 
                len(self._rooms))
        for room in self._rooms:
            logger.debug(self.neuron_name + ":       %s",self._rooms[room]['name'])
           
        # Categories   
        logger.debug(self.neuron_name + ": No. of Categories: %d", 
                len(self._controls)) 
        sum = 0
        for cat in self._controls:
            logger.debug(self.neuron_name + ":       %s",self._controls[cat]['name']) 
            sum = sum + len(self._controls[cat]['controls'])
        
        # Controls 
        logger.debug(self.neuron_name + ": Supported Types: %d", 
                len(self.TYPE_SWITCH) + len(self.TYPE_LIGHTCONTROL) +
                len(self.TYPE_JALOUSIE))
        for cat in self.TYPE_SWITCH:
                 logger.debug(self.neuron_name + ":       %s",  cat)
        for cat in self.TYPE_LIGHTCONTROL:
                 logger.debug(self.neuron_name + ":       %s",  cat)
        for cat in self.TYPE_JALOUSIE:
                 logger.debug(self.neuron_name + ":       %s",  cat)                 
     
        logger.debug(self.neuron_name + ": Defined Elements: %d", 
                sum)               
        logger.debug(self.neuron_name + ": (This is a list of supported "+
                "elements. There might be more elements defined in your " +
                "strcuture definition.)")
                
        for cat in self._controls:
            subcontrol = self._controls[cat]['controls']
            for controls in subcontrol:               
                logger.debug(self.neuron_name + ":       %s [%s, %s] in %s %s",
                    subcontrol[controls]['name'],  
                    subcontrol[controls]['type'],
                    self._controls[cat]['name'],   
                    self._roomtitle, 
                    self._rooms[subcontrol[controls]['room']]['name']) 
                
    def load_config(self):
        """
        Load the JSON Config File of the loxone miniserver.

        :return: true if config is loaded and parsed, false otherwise

        """
        # load structure definition
# TODO: [Feature] config should be cached and only loaded when needed
        try:
            r = requests.get("http://"+self._host +
                             self.STRUCTUREDEF, auth=(self._user,
                                                      self._password))
        except requests.ConnectionError:
            logger.debug(self.neuron_name +
                         ': Structure Definition Request failed.')
            return False

        try:
            r.raise_for_status()
            raw_info = r.json()['msInfo']
            raw_rooms = r.json()['rooms']
            raw_controls = r.json()['controls']
            raw_cats = r.json()['cats']
        except requests.exceptions.HTTPError:
            logger.debug(self.neuron_name +
                         ': Structure Definition Request failed with \
                response: %r',
                         r.text)
            return False
        except requests.exceptions.RequestException:
            logger.debug(self.neuron_name +
                         ': Structure Definition Request failed.')
            return False
        except ValueError as e:
            logger.debug(self.neuron_name +
                         ': Structure Definition cannot be loaded,'
                         'response: %s',
                         e.args[0])
            return False
        except KeyError:
            logger.debug(self.neuron_name +
                         ': Structure Definition cannot be loaded. KeyError.')
            return False

        # Parse structure
        try:
            # Get Info
            self._language = raw_info['languageCode']
            self._location = raw_info['location']
            self._roomtitle = raw_info['roomTitle']
            
            # Get rooms
            self._rooms = {}
            for room in raw_rooms:
                self._rooms[room] = {"name": raw_rooms[room]['name'],
                                     "uid": raw_rooms[room]['uuid']}

            # Get categories
            self._controls = {}
            for cat in raw_cats:
                self._controls[cat] = {"name": raw_cats[cat]['name'],
                                       "uid": raw_cats[cat]['uuid'],
                                       "type": raw_cats[cat]['type'],
                                       "controls": {}}

            # fill controls
            self.extract_controls(raw_controls)

        except KeyError:
            logger.debug(self.neuron_name +
                                ': Structure Definition cannot be parsed. '+
                                'KeyError.'
                                  )
            return False
# TODO: FIX Language check
        # Check Language
        # try:
        #    language = self.profile['language']
        # except KeyError:
        #    language = 'en-US'
        # if language.split('-')[1]==self._language:
        #    raise ValueError("Home automation language is %s. But your
        # profile language is set to %s",self._language,language)

        # debug print
        #pprint.pprint(self._controls)

        #pprint.pprint(self._rooms)

        return True

    def extract_controls(self, jsonconfig):
        """
        Parse the given JSON and extract the control information.

        :param jsonconfig: controls block of the json file

        """       
        
        # Step though each entry
        for control in jsonconfig:
                if jsonconfig[control]['type'] in self.TYPE_SWITCH:
                    self._controls[jsonconfig[control]['cat']][
                        'controls'][control] = {
                        "name": jsonconfig[control]['name'],
                        "uidAction": jsonconfig[control]['uuidAction'],
                        "room": jsonconfig[control]['room'],
                        "type": jsonconfig[control]['type']}
                elif jsonconfig[control]['type'] in self.TYPE_LIGHTCONTROL:
                        subcontrols = jsonconfig[control]['subControls']
                        for subcontrol in subcontrols:
                            if subcontrols[subcontrol]['type'] == "Switch":
                                self._controls[jsonconfig[control]['cat']][
                                    'controls'][subcontrol] = {
                                    "name": subcontrols[subcontrol]['name'],
                                    "uidAction": subcontrols[subcontrol][\
                                        'uuidAction'],
                                    "room": jsonconfig[control]['room'],
                                    "type": subcontrols[subcontrol]['type']}
                elif jsonconfig[control]['type'] in self.TYPE_JALOUSIE:
                    self._controls[jsonconfig[control]['cat']][
                        'controls'][control] = {
                        "name": jsonconfig[control]['name'],
                        "uidAction": jsonconfig[control]['uuidAction'],
                        "room": jsonconfig[control]['room'],
                        "type": jsonconfig[control]['type']}

                # IRoomController
                # InfoOnlyAnalog
        return
