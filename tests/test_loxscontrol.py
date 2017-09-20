# -*- coding: utf-8 -*-
"""TestCase for LoxSControl Class."""
import unittest
import mock
import logging

from kalliope.core.NeuronModule import MissingParameterException
from loxscontrol import Loxscontrol

logging.basicConfig()
logger = logging.getLogger("kalliope.neuron.loxscontrol")
#logger.setLevel(logging.DEBUG)


class TestLoxSControl(unittest.TestCase):

    """Unittest TestCase for LoxSControl."""

    def setUp(self):
        """
            Set-up Testenvironment.

            :return:

        """
        self.expected_result = "hello, this is a replaced word"
        # this allow us to run the test from an IDE and from the root with
        # python -m unittest Tests.TestNeuronModule

        # define some parameters
        self.lxms_ip = "127.0.0.1"
        self.lxms_noip = "no-ip"
        self.lxms_user = "loxoneuser"
        self.lxms_password = "loxonepassword"
        self.controls = {u'0c10052e': {'controls': {u'0c119829':
                         {'name': u'K\xfcche Arbeitsfl\xe4che',
                          'room': u'0ceefd17',
                          'type': u'Switch',
                          'uidAction': u'0c119829'}},
            'name': u'Light',
            'type': u'lights',
            'uid': u'0c10052e'},
            u'0c10053e': {'controls': {u'0c11982f':
                                       {'name': u'Living room',
                                        'room': u'0ceefd1d',
                                        'type': u'Jalousie',
                                        'uidAction': u'0c11982f'},
                                       u'0c11982d': {'name': u'Living room 2',
                                                     'room': u'0ceefd1d',
                                                     'type': u'Jalousie',
                                                     'uidAction': u'0c11982d'
                                                     }},
                          'name': u'Shading',
                          'type': u'shading',
                          'uid': u'0c10053e'},
            u'0c100510': {'controls':   {},
                          'name': u'Something',
                          'type': u'undefined',
                          'uid': u'0c100510'}}

        self.rooms = { u'0ceefd17': {'name': u'K\xfcche', 
                                'uid': u'0ceefd17'}, 
                                u'0ceefd1d': {'name':  u'Living room', 
                                'uid': u'0ceefd17'} 
                                }

        self.change_newstate = "on"

        self.lxstructuredef = {u'0c11982f': {u'name': u'Light', u'isFavorite': False,
            u'isSecured': False, u'cat': u'0c10052e', 
            u'states': {u'active': u'0d01671c'}, 
            u'uuidAction': u'0d01671c', 
            u'defaultRating': 0,
            u'type': u'Switch', 
            u'room': u'0c10052e'}, 
            u'0c101c69': {u'name': u'K\xfcche', u'isFavorite': False, 
            u'isSecured': False, u'cat': u'0c10052e', 
            u'states': {u'down': u'0c101c69', 
            u'position': u'0c101c69', 
            u'up': u'0c101c69', 
            u'shadePosition': u'0c101c69'}, 
            u'uuidAction': u'0c101c69', 
            u'defaultRating': 0, u'details': {u'animation': 1, 
            u'isAutomatic': False}, u'type': u'Jalousie', 
            u'room': u'0ceefd17'}            
            }

    def test_parameters(self):
        """Test for all combinations of missing parameters."""

        def run_test(parameters_to_test):
            """Expect an assert while initilising class"""
            with self.assertRaises(MissingParameterException):
                Loxscontrol(**parameters_to_test)

        # empty
        parameters = dict()
        run_test(parameters)

        # missing loxoneuser
        parameters = {
            "lx_ip": self.lxms_ip,
            "lx_password": self.lxms_password
        }
        run_test(parameters)

        # missing loxone_ip
        parameters = {
            "lx_user": self.lxms_user,
            "lx_password": self.lxms_password
        }
        run_test(parameters)

        # missing loxone_password
        parameters = {
            "lx_user": self.lxms_user,
            "lx_ip": self.lxms_ip
        }
        run_test(parameters)

        # no config given, no connection -> missing config
        parameters = {
            "lx_user": self.lxms_user,
            "lx_ip": self.lxms_ip,
            "lx_password": self.lxms_password
        }
        run_test(parameters)

        # no config given, wrong ip -> missing config
        parameters = {
            "lx_user": self.lxms_user,
            "lx_ip": self.lxms_noip,
            "lx_password": self.lxms_password
        }
        run_test(parameters)

        # nothing to do
        parameters = {
            "lx_user": self.lxms_user,
            "lx_ip": self.lxms_noip,
            "lx_password": self.lxms_password,
            "lx_structuredef": self.controls
        }
        run_test(parameters)

        # nothing to do
        parameters = {
            "lx_user": self.lxms_user,
            "lx_ip": self.lxms_noip,
            "lx_password": self.lxms_password,
            "lx_structuredef": self.controls
        }
        run_test(parameters)
        
    def test_get(self):
        """Test get functions."""        
        
        parameters = {
            "lx_user": self.lxms_user,
            "lx_password": self.lxms_password,
            "lx_ip": self.lxms_ip,
            "lx_structuredef": self.controls,
            "control_name":  u'K\xfcche Arbeitsfl\xe4che',
            "newstate": self.change_newstate        
        }
       
        with mock.patch("requests.get"):
                loxone_test = Loxscontrol(**parameters)
                loxone_test._rooms = self.rooms
 
                ###############
                # Test get_type_by_uuid
                # Test Categeories
                self.assertEqual(loxone_test.get_type_by_uuid('0c10052e'), loxone_test.CAT_LIGTH)
                self.assertEqual(loxone_test.get_type_by_uuid('0c10053e'), loxone_test.CAT_JALOUSIE)    
                self.assertEqual(loxone_test.get_type_by_uuid('0c100510'), loxone_test.CAT_UNDEF)
                
                # Test Types
                self.assertTrue(loxone_test.get_type_by_uuid('0c119829') in loxone_test.TYPE_SWITCH)
                self.assertTrue(loxone_test.get_type_by_uuid('0c11982d') in loxone_test.TYPE_JALOUSIE)

                # Test Rooms
                self.assertEqual(loxone_test.get_type_by_uuid('0ceefd17'), loxone_test.CAT_ROOM)

                # Test not found
                self.assertTrue(loxone_test.get_type_by_uuid('not a valid uuid') is None)

                ################
                # Test get_name_by_uuid
                # Test Types
                self.assertEqual(loxone_test.get_name_by_uuid('0c10052e'), u'Light')
                self.assertEqual(loxone_test.get_name_by_uuid('0c10053e'), u'Shading')

                # Test Controls
                self.assertEqual(loxone_test.get_name_by_uuid('0c119829'),  u'K\xfcche Arbeitsfl\xe4che')

                # Test Rooms
                self.assertEqual(loxone_test.get_name_by_uuid('0ceefd17'), u'K\xfcche')    
    
                # Test not found
                self.assertTrue(loxone_test.get_name_by_uuid('not a valid uuid') is None)    

                ################
                # Test get_controluuid_by_name
                # Test Control
                self.assertEqual(loxone_test.get_controluuid_by_name(u'K\xfcche Arbeitsfl\xe4che'),'0c119829')
                self.assertEqual(loxone_test.get_controluuid_by_name(u'Living room 2'),u'0c11982d')

                # Categories are not working
                self.assertEqual(loxone_test.get_controluuid_by_name(u'Light'), None)  
                # Rooms are not working               
                self.assertEqual(loxone_test.get_controluuid_by_name( u'K\xfcche'), None)
                
                
                

    def test_change_by_name(self):
        """Test changing a control element by its name."""
        def run_test(parameters,  expected_uuid,  expected_state):
            """
                Initialise class, check if Miniserver API is called correctly.

                :return:

            """
            with mock.patch("requests.get") as mock_requests_get:
                loxone_test = Loxscontrol(**parameters)
                self.assertEqual(loxone_test.message["status_code"],
                                 expected_state)
                if expected_uuid is not None:
                    mock_requests_get.\
                        assert_called_once_with("http://" +
                                                self.lxms_ip +
                                                Loxscontrol.SPSIO +
                                                "0c119829" + "/" +
                                                self.change_newstate,
                                                auth=(self.lxms_user,
                                                      self.lxms_password))
                mock_requests_get.reset_mock()

        # change by name, missing state
        parameters = {
            "lx_user": self.lxms_user,
            "lx_password": self.lxms_password,
            "lx_ip": self.lxms_ip,
            "lx_structuredef": self.controls,
            "control_name":  u'K\xfcche Arbeitsfl\xe4che',
        }
        expected_uuid = None
        expected_state = "IncompleteRequest"
        run_test(parameters,  expected_uuid,  expected_state)

        # change by name with success
        parameters["newstate"] = self.change_newstate
        expected_uuid = "0c119829"
        expected_state = "Complete"
        run_test(parameters,  expected_uuid,  expected_state)

        # change by name with success
        parameters["control_name"] = "This_name_is_missing_in_definition"
        expected_uuid = None
        expected_state = "StateChangeError"
        run_test(parameters,  expected_uuid,  expected_state)

    def test_load_config(self):
        """Test loading the structure definition of the miniserver."""

        # no structure given -> neurons tries to load structure
        # -> we catch this
        parameters = {
            "lx_user": self.lxms_user,
            "lx_password": self.lxms_password,
            "lx_ip": self.lxms_ip,
            "control_name": "name"
        }
        with mock.patch("requests.get") as mock_requests_get:
                self.loxone_test = Loxscontrol(**parameters)
                mock_requests_get.\
                    assert_called_once_with("http://" +
                                            self.lxms_ip +
                                            Loxscontrol.STRUCTUREDEF,
                                            auth=(self.lxms_user,
                                                  self.lxms_password))
                mock_requests_get.reset_mock()

    def test_extract_controls(self):
        """Test json import of structuredef."""
        pass
# TODO: a test which feeds a json and retrieves the controls
        # mock request get call and return a json file

if __name__ == '__main__':
#suite = unittest.TestLoader().loadTestsFromTestCase(TestLoxSControl)
#unittest.TextTestRunner(verbosity=2).run(suite)
     unittest.main()
