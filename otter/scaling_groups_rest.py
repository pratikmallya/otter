""" Scaling groups REST mock API"""

from twisted.web.resource import Resource
from util.schema import validate_body
from util.fault import fails_with, succeeds_with
from klein import resource, route
from twisted.internet import defer
import json
from otter.models.interface import \
    scaling_group_config_schema, NoSuchScalingGroupError
from otter.util.schema import InvalidJsonError
from jsonschema import ValidationError

_store = None
_urlRoot = 'http://127.0.0.1/v1.0'


def get_store():
    """
    :return: the inventory to be used in forming the REST responses
    :rtype: :class:`cupboard.interface.IInventory` provider
    """
    global _store
    if _store is None:
        from otter.models.mock import MockScalingGroupCollection
        _store = MockScalingGroupCollection()
    return _store


def get_url_root():
    """
    Get the URL root
    :return: string containing the URL root
    """
    global _urlRoot
    return _urlRoot


def set_store(i_store_provider):
    """
    Sets the inventory to use in forming the REST responses

    :param i_inventory_provider: the inventory to be used in forming the REST
        responses
    :type i_inventory_provider: :class:`cupboard.interface.IInventory` provider

    :return: None
    """
    global _store
    _store = i_store_provider

exception_codes = {
    ValidationError: 400,
    InvalidJsonError: 400,
    NoSuchScalingGroupError: 404
}


def _format_groups(groups):
    res = {}
    for colo in groups:
        res[colo] = map(lambda format: {'id': format.uuid,
                                        'region': format.region}, groups[colo])
    return res


@route('/<string:tenantid>/scaling_groups/<string:coloid>/<string:groupid>'
       '/servers/<string:serverid>', methods=['DELETE'])
def delete_scaling_group_servers(request, tenantid, coloid, groupid, serverid):
    """
    Deletes a server from the scaling group

    Returns a string and 200
    """
    return defer.fail(NotImplementedError())


@route('/<string:tenantid>/scaling_groups/<string:coloid>/<string:groupid>'
       '/servers', methods=['GET'])
def get_scaling_group_servers(request, tenantid, coloid, id):
    """Get a list of the servers in a scaling group.

    Response format to be defined
    Returns a string and 200

    """
    return defer.fail(NotImplementedError())


@route('/<string:tenantid>/scaling_groups/<string:coloid>/<string:groupid>',
       methods=['GET'])
@fails_with(exception_codes)
@succeeds_with(200)
def view_config_for_scaling_group(request, tenantid, coloid, groupid):
    """
    Get config for a scaling group -- gets a dict from the storage
    engine and returns it to the user serialized as JSON

    Returns a deferred string

    The response looks mostly like this:
    {'name': 'blah', 'cooldown': 60, 'min_entities': 0}

    """
    rec = get_store().get_scaling_group(tenantid, coloid, groupid)
    deferred = defer.maybeDeferred(rec.view_config)
    deferred.addCallback(json.dumps)
    return deferred


@route('/<string:tenantid>/scaling_groups/<string:coloid>/<string:groupid>',
       methods=['PUT'])
@fails_with(exception_codes)
@succeeds_with(204)
@validate_body(scaling_group_config_schema)
def edit_scaling_group(request, tenantid, coloid, groupid, data):
    """
    Edit config for a scaling group.

    The request looks like: {'name': 'blah', 'cooldown': 60, 'min_entities': 0}
    and the response will be a 204

    The exact update cases are still up in the air -- what happens
    with defaults?

    returns a deferred for completion

    """
    rec = get_store().get_scaling_group(tenantid, coloid, groupid)
    deferred = defer.maybeDeferred(rec.update_config, data)
    return deferred


@route('/<string:tenantid>/scaling_groups/<string:coloid>/<string:groupid>',
       methods=['DELETE'])
@fails_with(exception_codes)
@succeeds_with(204)
def delete_scaling_group(request, tenantid, coloid, groupid):
    """
    Delete a scaling group.

    returns a deferred for completion
    """
    deferred = defer.maybeDeferred(get_store().delete_scaling_group,
                                   tenantid, coloid, groupid)
    return deferred


@route('/<string:tenantid>/scaling_groups',  methods=['GET'])
@fails_with(exception_codes)
@succeeds_with(200)
def get_all_scaling_groups(request, tenantid):
    """
    Get a list of all scaling groups in all colos

    Returns a deferred
    [{'id': 0, 'region': 'dfw'},
     {'id': 1, 'region': 'iad'}]
    as a deferred

    """
    deferred = defer.maybeDeferred(get_store().list_scaling_groups, tenantid)
    deferred.addCallback(_format_groups)
    deferred.addCallback(json.dumps)
    return deferred


@route('/<string:tenantid>/scaling_groups/<string:coloid>',  methods=['GET'])
@fails_with(exception_codes)
@succeeds_with(200)
def get_scaling_groups(request, tenantid, coloid):
    """
    Get a list of scaling groups for a given colo

    Returns a list of scaling groups, looking like:
    [{'id': 0, 'region': 'dfw'},
     {'id': 1, 'region': 'dfw'}]
    as a deferred

    """
    deferred = defer.maybeDeferred(get_store().list_scaling_groups,
                                   tenantid, coloid)
    deferred.addCallback(_format_groups)
    deferred.addCallback(json.dumps)
    return deferred


@route('/<string:tenantid>/scaling_groups/<string:coloid>', methods=['POST'])
@fails_with(exception_codes)
@succeeds_with(201)
@validate_body(scaling_group_config_schema)
def create_new_scaling_group(request, tenantid, coloid, data):
    """Create a new scaling group.

    Returns a deferred, with the URL in the location header

    """

    def send_redirect(uuid):
        request.setHeader("Location",
                          "{0}/{1}/scaling_groups/{2}/{3}/".
                          format(get_url_root(), tenantid, coloid, uuid))

    deferred = defer.maybeDeferred(get_store().create_scaling_group, tenantid,
                                   coloid, data)
    deferred.addCallback(send_redirect)
    return deferred


root = Resource()
root.putChild('v1.0', resource())
