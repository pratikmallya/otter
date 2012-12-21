"""
Tests for :mod:`otter.jsonschema.scaling_group`
"""
from copy import deepcopy

from twisted.trial.unittest import TestCase
from jsonschema import Draft3Validator, validate, ValidationError

from otter.json_schema import scaling_group


class ScalingGroupConfigTestCase(TestCase):
    """
    Simple verification that the JSON schema for scaling groups is correct.
    """
    def test_schema_valid(self):
        """
        The schema itself is valid Draft 3 schema
        """
        Draft3Validator.check_schema(scaling_group.config)

    def test_all_properties_have_descriptions(self):
        """
        All the properties in the schema should have descriptions
        """
        for property_name in scaling_group.config['properties']:
            prop = scaling_group.config['properties'][property_name]
            self.assertTrue('description' in prop)

    def test_valid_examples_validate(self):
        """
        The examples in the config examples all validate.
        """
        for example in scaling_group.config_examples:
            validate(example, scaling_group.config)

    def test_extra_values_does_not_validate(self):
        """
        Providing non-expected properties will fail validate.
        """
        invalid = {
            'name': 'who',
            'cooldown': 60,
            'minEntities': 1,
            'what': 'not expected'
        }
        self.assertRaisesRegexp(ValidationError, "Additional properties",
                                validate, invalid, scaling_group.config)

    def test_long_name_value_does_not_validate(self):
        """
        The name must be less than or equal to 256 characters.
        """
        invalid = {
            'name': ' ' * 257,
            'cooldown': 60,
            'minEntities': 1,
        }
        self.assertRaisesRegexp(ValidationError, "is too long",
                                validate, invalid, scaling_group.config)

    def test_invalid_metadata_does_not_validate(self):
        """
        Metadata keys and values must be strings of less than or equal to 256
        characters.  Anything else will fail to validate.
        """
        base = {
            'name': "stuff",
            'cooldown': 60,
            'minEntities': 1
        }
        invalids = [
            # because Draft 3 doesn't support key length, so it's a regexp
            ({'key' * 256: ""}, "Additional properties"),
            ({'key': "value" * 256}, "is too long"),
            ({'key': 1}, "not of type"),
            ({'key': None}, "not of type")
        ]
        for invalid, error_regexp in invalids:
            base['metadata'] = invalid
            self.assertRaisesRegexp(ValidationError, error_regexp,
                                    validate, base, scaling_group.config)


class GeneralLaunchConfigTestCase(TestCase):
    """
    Verification that the general JSON schema for launch configs is correct.
    """
    def test_schema_valid(self):
        """
        The schema itself is a valid Draft 3 schema
        """
        Draft3Validator.check_schema(scaling_group.launch_config)

    def test_must_have_lauch_server_type(self):
        """
        Without a launch server type, validation fails
        """
        self.assertRaisesRegexp(
            ValidationError, "'type' is a required property",
            validate, {"args": {"server": {}}}, scaling_group.launch_config)

    def test_invalid_launch_config_type_does_not_validate(self):
        """
        If a launch config type is provided that is not enum-ed, validation
        fails
        """
        self.assertRaisesRegexp(ValidationError, 'not of type',
                                validate, {'type': '_testtesttesttest'},
                                scaling_group.launch_config)

    def test_other_launch_config_type(self):
        """
        Test use of union types by adding another launch config type and
        seeing if that validates.
        """
        other_type = {
            "type": "object",
            "description": "Tester launch config type",
            "properties": {
                "type": {
                    "enum": ["_testtesttesttest"]
                },
                "args": {}
            }
        }
        schema = deepcopy(scaling_group.launch_config)
        schema['type'].append(other_type)
        validate({"type": "_testtesttesttest", "args": {"what": "who"}},
                 schema)


class ServerLaunchConfigTestCase(TestCase):
    """
    Simple verification that the JSON schema for launch server launch configs
    is correct.
    """
    def test_valid_examples_validate(self):
        """
        The launch server config examples all validate.
        """
        for example in scaling_group.launch_server_config_examples:
            validate(example, scaling_group.launch_config)

    def test_invalid_load_balancer_does_not_validate(self):
        """
        Load balancers need to have 2 values: loadBalancerId and port.
        """
        base = {
            "type": "launch_server",
            "args": {
                "server": {}
            }
        }
        invalids = [
            {'loadBalancerId': '', 'port': 80},
            {'loadBalancerId': 3, 'port': '80'}
        ]
        for invalid in invalids:
            base["args"]["loadBalancers"] = [invalid]
            # the type fails ot valdiate because of 'not of type'
            self.assertRaisesRegexp(ValidationError, 'not of type', validate,
                                    base, scaling_group.launch_server)
            # because the type schema fails to validate, the config schema
            # fails to validate because it is not the given type
            self.assertRaisesRegexp(ValidationError, 'not of type', validate,
                                    base, scaling_group.launch_config)

    def test_duplicate_load_balancers_do_not_validate(self):
        """
        If the same load balancer config appears twice, the launch config
        fails to validate.
        """
        invalid = {
            "type": "launch_server",
            "args": {
                "server": {},
                "loadBalancers": [
                    {'loadBalancerId': 1, 'port': 80},
                    {'loadBalancerId': 1, 'port': 80}
                ]
            }
        }
        # the type fails ot valdiate because of the load balancers are not
        # unique
        self.assertRaisesRegexp(ValidationError, 'non-unique elements',
                                validate, invalid, scaling_group.launch_server)
        # because the type schema fails to validate, the config schema
        # fails to validate because it is not the given type
        self.assertRaisesRegexp(ValidationError, 'not of type',
                                validate, invalid, scaling_group.launch_config)

    def test_unspecified_args_do_not_validate(self):
        """
        If random attributes to args are provided, the launch config fails to
        validate
        """
        invalid = {
            "type": "launch_server",
            "args": {
                "server": {},
                "hat": "top"
            }
        }
        # the type fails ot valdiate because of the additional 'hat' property
        self.assertRaisesRegexp(ValidationError, 'Additional properties',
                                validate, invalid, scaling_group.launch_server)
        # because the type schema fails to validate, the config schema
        # fails to validate because it is not the given type
        self.assertRaisesRegexp(ValidationError, 'not of type',
                                validate, invalid, scaling_group.launch_config)

    def test_no_args_do_not_validate(self):
        """
        If no arguments are provided, the launch config fails to validate
        """
        invalid = {
            "type": "launch_server",
            "args": {}
        }
        self.assertRaisesRegexp(
            ValidationError, "'server' is a required property",
            validate, invalid, scaling_group.launch_server)
        self.assertRaisesRegexp(ValidationError, 'not of type',
                                validate, invalid, scaling_group.launch_config)


class ScalingPolicyTestCase(TestCase):
    """
    Simple verification that the JSON schema for scaling policies is correct.
    """
    def test_schema_valid(self):
        """
        The schema itself is a valid Draft 3 schema
        """
        Draft3Validator.check_schema(scaling_group.policy)

    def test_valid_examples_validate(self):
        """
        The scaling policy examples all validate.
        """
        for example in scaling_group.policy_examples:
            validate(example, scaling_group.policy)

    def test_either_change_or_changePercent_or_steadyState(self):
        """
        A scaling policy can have the attribute "change" or "changePercent" or
        "steadyState", but not any combination thereof
        """
        one_only = ("change", "changePercent", "steadyState")
        for combination in ((0, 1), (0, 2), (1, 2), (0, 1, 2)):
            invalid = {
                "name": "meh",
                "cooldown": 5,
            }
            for index in combination:
                invalid[one_only[index]] = 5
            self.assertRaisesRegexp(
                ValidationError, 'not of type',
                validate, invalid, scaling_group.policy)

    def test_set_steady_state_must_not_be_negative(self):
        """
        Cannot set the steady state to a negative number
        """
        invalid = {
            "name": "",
            "steadyState": -1,
            "cooldown": 5
        }
        self.assertRaisesRegexp(
            ValidationError, 'minimum',
            validate, invalid, scaling_group.policy)

    def test_no_other_properties_valid(self):
        """
        Scaling policy can only have the following properties: name,
        change/changePercent, cooldown, and capabilityUrls.  Any other property
        results in an error.
        """
        invalid = {
            "name": "",
            "change": 5,
            "cooldown": 5,
            "poofy": False
        }
        self.assertRaisesRegexp(
            ValidationError, 'not of type',
            validate, invalid, scaling_group.policy)


class CreateScalingGroupTestCase(TestCase):
    """
    Simple verification that the JSON schema for creating a scaling group is
    correct.
    """
    def test_schema_valid(self):
        """
        The schema itself is a valid Draft 3 schema
        """
        Draft3Validator.check_schema(scaling_group.create_group)

    def test_valid_examples_validate(self):
        """
        The scaling policy examples all validate.
        """
        for example in scaling_group.create_group_examples:
            validate(example, scaling_group.create_group)

    def test_wrong_launch_config_fails(self):
        """
        Not including a launchConfiguration or including an invalid ones will
        fail to validate.
        """
        invalid = {'groupConfiguration': scaling_group.config_examples[0]}
        self.assertRaisesRegexp(
            ValidationError, 'launchConfiguration',
            validate, invalid, scaling_group.create_group)
        invalid['launchConfiguration'] = {}
        self.assertRaises(ValidationError,
                          validate, invalid, scaling_group.create_group)

    def test_wrong_group_config_fails(self):
        """
        Not including a groupConfiguration or including an invalid ones will
        fail to validate.
        """
        invalid = {'launchConfiguration':
                   scaling_group.launch_server_config_examples[0]}
        self.assertRaisesRegexp(
            ValidationError, 'groupConfiguration',
            validate, invalid, scaling_group.create_group)
        invalid['groupConfiguration'] = {}
        self.assertRaises(ValidationError,
                          validate, invalid, scaling_group.create_group)

    def test_wrong_scaling_policy_fails(self):
        """
        An otherwise ok creation blob fails if the provided scaling policies
        are wrong.
        """
        self.assertRaises(
            ValidationError, validate, {
                'groupConfiguration': scaling_group.config_examples[0],
                'launchConfiguration':
                scaling_group.launch_server_config_examples[0],
                'scalingPolicies': [{}]
            }, scaling_group.create_group)
