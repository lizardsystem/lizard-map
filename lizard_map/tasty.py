from tastypie import fields
from tastypie.resources import Resource


class MapPlugin(Resource):
    #class Meta:
    #    resource_name = 'plugin'

    def obj_get_list(self, request=None, filters=None):
        print filters
        return []

