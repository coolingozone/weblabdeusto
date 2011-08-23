#!/usr/bin/env python
#-*-*- encoding: utf-8 -*-*-
#
# Copyright (C) 2005-2009 University of Deusto
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# This software consists of contributions made by many individuals, 
# listed below:
#
# Author: Pablo Orduña <pablo@ordunya.com>
# 


import unittest

import test.unit.configuration as configuration_module
import voodoo.configuration.ConfigurationManager as ConfigurationManager

import weblab.data.experiments.ExperimentInstanceId as ExperimentInstanceId

from weblab.data.experiments.ExperimentId import ExperimentId
from weblab.core.coordinator.Resource import Resource
from weblab.core.coordinator.Coordinator import Coordinator
import weblab.core.coordinator.resource_manager as ResourcesManager
import weblab.core.coordinator.db as CoordinationDatabaseManager
import weblab.core.coordinator.model as CoordinatorModel
import weblab.core.coordinator.exc as CoordExc

class ResourcesManagerTestCase(unittest.TestCase):
    def setUp(self):
        self.cfg_manager = ConfigurationManager.ConfigurationManager()
        self.cfg_manager.append_module(configuration_module)

        coordinator = Coordinator(None, self.cfg_manager)
        coordinator._clean()

        coordination_database = CoordinationDatabaseManager.CoordinationDatabaseManager(self.cfg_manager)
        self.session_maker = coordination_database.session_maker
        self.resources_manager = ResourcesManager.ResourcesManager(self.session_maker)
        self.resources_manager._clean()

    def test_add_resource(self):
        session = self.session_maker()
        try:
            resource_types = session.query(CoordinatorModel.ResourceType).all()
            self.assertEquals(0, len(resource_types), "No resource expected in the beginning of the test")

            self.resources_manager.add_resource(session, Resource("type", "instance"))
            self._check_resource_added(session)
            session.commit()
        finally:
            session.close()

        # Can be executed twice without conflicts

        session = self.session_maker()
        try:
            self.resources_manager.add_resource(session, Resource("type", "instance"))
            self._check_resource_added(session)
            session.commit()
        finally:
            session.close()

    def _check_resource_added(self, session):
        resource_types = session.query(CoordinatorModel.ResourceType).all()
        self.assertEquals(1, len(resource_types))

        resource_type = resource_types[0]
        self.assertEquals("type", resource_type.name)

        resource_instances = resource_type.instances
        self.assertEquals(1, len(resource_instances))

        resource_instance = resource_instances[0]
        self.assertEquals("instance", resource_instance.name)
        self.assertEquals(resource_type, resource_instance.resource_type)

        slot = resource_instance.slot
        self.assertNotEquals(None, slot)
        self.assertEquals(resource_instance, slot.resource_instance)

    def test_add_experiment_instance_id(self):
        session = self.session_maker()
        try:
            resource_types = session.query(CoordinatorModel.ResourceType).all()
            self.assertEquals(0, len(resource_types), "No resource expected in the beginning of the test")
    
            exp_id = ExperimentInstanceId.ExperimentInstanceId("exp1","ud-pld","PLD Experiments")
            self.resources_manager.add_experiment_instance_id(session, "laboratory1:WL_SERVER1@WL_MACHINE1", exp_id, Resource("type", "instance"))
            self._check_resource_added(session)
            self._check_experiment_instance_id_added(session)
            session.commit()
        finally:
            session.close()

    def test_add_experiment_instance_id_redundant(self):
        session = self.session_maker()
        try:
            resource_types = session.query(CoordinatorModel.ResourceType).all()
            self.assertEquals(0, len(resource_types), "No resource expected in the beginning of the test")
    
            exp_id = ExperimentInstanceId.ExperimentInstanceId("exp1","ud-pld","PLD Experiments")
            self.resources_manager.add_experiment_instance_id(session, "laboratory1:WL_SERVER1@WL_MACHINE1", exp_id, Resource("type", "instance"))

            # No problem in adding twice the same
            self.resources_manager.add_experiment_instance_id(session, "laboratory1:WL_SERVER1@WL_MACHINE1", exp_id, Resource("type", "instance"))

            # Everything is all right
            self._check_resource_added(session)
            self._check_experiment_instance_id_added(session)
    
            # However, we can't add another time the same experiment instance with a different laboratory id:
            self.assertRaises(CoordExc.InvalidExperimentConfigException,
                    self.resources_manager.add_experiment_instance_id,
                    session, "laboratory2:WL_SERVER1@WL_MACHINE1", exp_id, Resource("type", "instance"))

            # Or the same experiment instance with a different resource instance:
            self.assertRaises(CoordExc.InvalidExperimentConfigException,
                    self.resources_manager.add_experiment_instance_id,
                    session, "laboratory1:WL_SERVER1@WL_MACHINE1", exp_id, Resource("type", "instance2"))

            session.commit()
        finally:
            session.close()


    def test_get_resource_instance_by_experiment_instance_id(self):
        session = self.session_maker()
        try:
            exp_id = ExperimentInstanceId.ExperimentInstanceId("exp1","ud-pld","PLD Experiments")
            self.resources_manager.add_experiment_instance_id(session, "laboratory1:WL_SERVER1@WL_MACHINE1", exp_id, Resource("type", "instance"))
            session.commit()
        finally:
            session.close()

        resource = self.resources_manager.get_resource_instance_by_experiment_instance_id(exp_id)
        expected_resource = Resource("type", "instance")
        self.assertEquals(expected_resource, resource)

    def test_get_resource_instance_by_experiment_instance_id_failing(self):
        session = self.session_maker()
        try:
            exp_id = ExperimentInstanceId.ExperimentInstanceId("exp1","ud-pld","PLD Experiments")
            self.resources_manager.add_experiment_instance_id(session, "laboratory1:WL_SERVER1@WL_MACHINE1", exp_id, Resource("type", "instance"))
            session.commit()
        finally:
            session.close()

        exp_invalid_type = ExperimentInstanceId.ExperimentInstanceId("exp1","ud-pld.invalid", "PLD Experiments")

        self.assertRaises( CoordExc.ExperimentNotFoundException, 
                            self.resources_manager.get_resource_instance_by_experiment_instance_id,
                            exp_invalid_type )

        exp_invalid_inst = ExperimentInstanceId.ExperimentInstanceId("exp.invalid","ud-pld", "PLD Experiments")
        self.assertRaises( CoordExc.ExperimentNotFoundException, 
                            self.resources_manager.get_resource_instance_by_experiment_instance_id,
                            exp_invalid_inst )

    def test_get_resource_types_by_experiment_id(self):
        session = self.session_maker()
        try:
            exp_id = ExperimentInstanceId.ExperimentInstanceId("exp1","ud-pld","PLD Experiments")
            self.resources_manager.add_experiment_instance_id(session, "laboratory1:WL_SERVER1@WL_MACHINE1", exp_id, Resource("type", "instance"))
            session.commit()
        finally:
            session.close()

        exp_type_id = ExperimentId("ud-pld", "PLD Experiments")
        resource_types = self.resources_manager.get_resource_types_by_experiment_id(exp_type_id)
        self.assertEquals(1, len(resource_types))
        self.assertTrue(u"type" in resource_types)

    def test_get_resource_types_by_experiment_id_error(self):
        session = self.session_maker()
        try:
            exp_id = ExperimentInstanceId.ExperimentInstanceId("exp1","ud-pld","PLD Experiments")
            self.resources_manager.add_experiment_instance_id(session, "laboratory1:WL_SERVER1@WL_MACHINE1", exp_id, Resource("type", "instance"))
            session.commit()
        finally:
            session.close()

        self.assertRaises(
                CoordExc.ExperimentNotFoundException,
                self.resources_manager.get_resource_types_by_experiment_id,
                ExperimentId("foo","bar")
            )

    def _check_experiment_instance_id_added(self, session):
        experiment_types = session.query(CoordinatorModel.ExperimentType).all()
        self.assertEquals(1, len(experiment_types))

        experiment_type = experiment_types[0]
        self.assertEquals("PLD Experiments", experiment_type.cat_name)
        self.assertEquals("ud-pld", experiment_type.exp_name)

        experiment_instances = experiment_type.instances
        self.assertEquals(1, len(experiment_instances))

        experiment_instance = experiment_instances[0]
        self.assertEquals("exp1", experiment_instance.experiment_instance_id)
        self.assertEquals(experiment_type, experiment_instance.experiment_type)

        resource_instance = experiment_instance.resource_instance
        self.assertEquals("instance", resource_instance.name)

        resource_type = resource_instance.resource_type
        self.assertTrue(resource_type in experiment_type.resource_types)
        self.assertTrue(experiment_type in resource_type.experiment_types)

    def test_remove_resource_instance_id(self):
        session = self.session_maker()
        try:
            exp_id = ExperimentInstanceId.ExperimentInstanceId("exp1","ud-pld","PLD Experiments")
            self.resources_manager.add_experiment_instance_id(session, "laboratory1:WL_SERVER1@WL_MACHINE1", exp_id, Resource("type", "instance"))

            experiment_instances = session.query(CoordinatorModel.ExperimentInstance).all()
            self.assertEquals(1, len(experiment_instances))

            self.resources_manager.remove_resource_instance_id(session, exp_id)

            experiment_instances = session.query(CoordinatorModel.ExperimentInstance).all()
            self.assertEquals(0, len(experiment_instances))

            session.commit()
        finally:
            session.close()

    def test_remove_resource_instance(self):
        session = self.session_maker()
        try:
            exp_id = ExperimentInstanceId.ExperimentInstanceId("exp1","ud-pld","PLD Experiments")
            resource_instance = Resource("type", "instance")
            self.resources_manager.add_experiment_instance_id(session, "laboratory1:WL_SERVER1@WL_MACHINE1", exp_id, resource_instance)

            # Checking that the resources are there
            experiment_instances = session.query(CoordinatorModel.ExperimentInstance).all()
            self.assertEquals(1, len(experiment_instances))
            resource_instances = session.query(CoordinatorModel.ResourceInstance).all()
            self.assertEquals(1, len(resource_instances))

            # Removing resource instance
            self.resources_manager.remove_resource_instance(session, resource_instance)

            # Checking that the resources are not there, neither the experiment instances
            resource_instances = session.query(CoordinatorModel.ResourceInstance).all()
            self.assertEquals(0, len(resource_instances))
            experiment_instances = session.query(CoordinatorModel.ExperimentInstance).all()
            self.assertEquals(0, len(experiment_instances))

            session.commit()
        finally:
            session.close()

    def test_list_resources(self):
        session = self.session_maker()
        try:
            exp_id1 = ExperimentInstanceId.ExperimentInstanceId("exp1","ud-pld","PLD Experiments")
            resource_instance1 = Resource("type1", "instance1")
            self.resources_manager.add_experiment_instance_id(session, "laboratory1:WL_SERVER1@WL_MACHINE1", exp_id1, resource_instance1)

            exp_id2 = ExperimentInstanceId.ExperimentInstanceId("exp2","ud-pld","PLD Experiments")
            resource_instance2 = Resource("type2", "instance1")
            self.resources_manager.add_experiment_instance_id(session, "laboratory1:WL_SERVER1@WL_MACHINE1", exp_id2, resource_instance2)
            session.commit()
        finally:
            session.close()

        resources = self.resources_manager.list_resources()
        self.assertEquals(2, len(resources))
        self.assertTrue('type1' in resources)
        self.assertTrue('type2' in resources)

    def test_list_experiments(self):
        session = self.session_maker()
        try:
            exp_id1 = ExperimentInstanceId.ExperimentInstanceId("exp1","ud-pld","PLD Experiments")
            resource_instance1 = Resource("type1", "instance1")
            self.resources_manager.add_experiment_instance_id(session, "laboratory1:WL_SERVER1@WL_MACHINE1", exp_id1, resource_instance1)

            exp_id2 = ExperimentInstanceId.ExperimentInstanceId("exp2","ud-pld","PLD Experiments")
            resource_instance2 = Resource("type2", "instance1")
            self.resources_manager.add_experiment_instance_id(session, "laboratory1:WL_SERVER1@WL_MACHINE1", exp_id2, resource_instance2)
            session.commit()
        finally:
            session.close()

        resources = self.resources_manager.list_experiments()
        self.assertEquals(1, len(resources))
        self.assertTrue(ExperimentId('ud-pld', 'PLD Experiments') in resources)

    def test_list_experiment_instance_ids_by_resource(self):
        session = self.session_maker()
        try:
            exp_id1 = ExperimentInstanceId.ExperimentInstanceId("exp1","ud-pld","PLD Experiments")
            resource_instance1 = Resource("type1", "instance1")
            self.resources_manager.add_experiment_instance_id(session, "laboratory1:WL_SERVER1@WL_MACHINE1", exp_id1, resource_instance1)

            exp_id2 = ExperimentInstanceId.ExperimentInstanceId("exp2","ud-pld","PLD Experiments")
            self.resources_manager.add_experiment_instance_id(session, "laboratory1:WL_SERVER1@WL_MACHINE1", exp_id2, resource_instance1)

            exp_id3 = ExperimentInstanceId.ExperimentInstanceId("exp3","ud-pld","PLD Experiments")
            resource_instance2 = Resource("type1", "instance2")
            self.resources_manager.add_experiment_instance_id(session, "laboratory1:WL_SERVER1@WL_MACHINE1", exp_id3, resource_instance2)

            session.commit()
        finally:
            session.close()

        experiment_instance_ids = self.resources_manager.list_experiment_instance_ids_by_resource(resource_instance1)
        self.assertEquals(2, len(experiment_instance_ids))
        self.assertTrue(ExperimentInstanceId.ExperimentInstanceId('exp1','ud-pld', 'PLD Experiments') in experiment_instance_ids)
        self.assertTrue(ExperimentInstanceId.ExperimentInstanceId('exp2','ud-pld', 'PLD Experiments') in experiment_instance_ids)


    def test_list_laboratories_addresses(self):
        session = self.session_maker()
        try:
            exp_id1 = ExperimentInstanceId.ExperimentInstanceId("exp1","ud-pld","PLD Experiments")
            resource_instance1 = Resource("type1", "instance1")
            self.resources_manager.add_experiment_instance_id(session, "laboratory1:WL_SERVER1@WL_MACHINE1", exp_id1, resource_instance1)

            # Repeating laboratory1, but a set is returned so no problem
            exp_id2 = ExperimentInstanceId.ExperimentInstanceId("exp2","ud-pld","PLD Experiments")
            resource_instance2 = Resource("type2", "instance1")
            self.resources_manager.add_experiment_instance_id(session, "laboratory1:WL_SERVER1@WL_MACHINE1", exp_id2, resource_instance2)

            exp_id3 = ExperimentInstanceId.ExperimentInstanceId("exp3","ud-pld","PLD Experiments")
            resource_instance3 = Resource("type2", "instance2")
            self.resources_manager.add_experiment_instance_id(session, "laboratory2:WL_SERVER1@WL_MACHINE1", exp_id3, resource_instance3)

            session.commit()
        finally:
            session.close()

        addresses = self.resources_manager.list_laboratories_addresses()
        self.assertEquals(2, len(addresses))
        self.assertTrue("laboratory1:WL_SERVER1@WL_MACHINE1" in addresses)
        self.assertEquals(2, len(addresses["laboratory1:WL_SERVER1@WL_MACHINE1"]))
        self.assertTrue(exp_id1 in addresses["laboratory1:WL_SERVER1@WL_MACHINE1"])
        self.assertTrue(exp_id2 in addresses["laboratory1:WL_SERVER1@WL_MACHINE1"])
        self.assertTrue("laboratory2:WL_SERVER1@WL_MACHINE1" in addresses)
        self.assertEquals(1, len(addresses["laboratory2:WL_SERVER1@WL_MACHINE1"]))
        self.assertTrue(exp_id3 in addresses["laboratory2:WL_SERVER1@WL_MACHINE1"])

        self.assertEquals(resource_instance1, addresses["laboratory1:WL_SERVER1@WL_MACHINE1"][exp_id1])
        self.assertEquals(resource_instance2, addresses["laboratory1:WL_SERVER1@WL_MACHINE1"][exp_id2])
        self.assertEquals(resource_instance3, addresses["laboratory2:WL_SERVER1@WL_MACHINE1"][exp_id3])

def suite():
    return unittest.makeSuite(ResourcesManagerTestCase)

if __name__ == '__main__':
    unittest.main()

