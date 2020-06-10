import requests
import json
import redis

__author__ = 'fmorales'

"""
Generic implementation of API REST interface:

usage:
    
    api = ApiRequest()
    result = api.get('url/to/test/1', motor='odoo')
    print (result)
    result = api.get('url/to/test/2', motor='graphql')
    print (result)
    
"""

DEFAULT = 'QA'
#import sqlite3

TTL = 28800 #12 horas de cache de la sesion
redis_cnx = redis.Redis(host='localhost', port=6379, db=0)

SERVICES = {
    'QA': {
        'odoo': {
            'host': 'host2odoo',
            'protocol': 'http',
            'port': '80',
            'ssl_check': False,
            'auth': {
                'api': '/web/session/authenticate',
                'method': requests.Session,
                'session_id': None,
                'credentials': json.dumps({
                        "params": {
                            "db": "dbodoo",
                            "login": "userodoo",
                            "password": "password"
                            }
                    })
                 },
            'header': {'content-type': 'application/json'},
            'default_data': json.dumps({}),
            'parser': None,

        },
        'graphql':{
            #TODO: Define this
        },
        'odoo12': {
            'host': 'hostodoo12',
            'protocol': 'http',
            'port': '80'
        }
    },
    'PD': {
        'odoo': {
            'host': 'host2odoo',
            'protocol': 'http',
            'port': '80',
            'ssl_check': False,
            'auth': {
                'api': '/web/session/authenticate',
                'method': requests.Session,
                'session_id': None,
                'credentials': json.dumps({
                        "params": {
                            "db": "dbodoo",
                            "login": "userodoo",
                            "password": "password"
                            }
                    })
                 },
            'header': {'content-type': 'application/json'},
            'default_data': json.dumps({}),
            'parser': None,

        },
        'graphql':{
            #TODO: Define this
        },
        'odoo12': {
            'host': 'hostodoo12',
            'protocol': 'http',
            'port': '80'
        }
    },
}

SERVICE = SERVICES[DEFAULT]

class ApiRequest:

    def __init__(self):
        pass
    def login(self, url, data, headers, service):
        '''
        :return: session id si corresponde
        '''
        call_auth = service.post(url=url, data=data, headers=headers)
        result = call_auth.json().get('result', None)
        if call_auth.ok and result:
            return result.get('session_id')

    def post(self, api=None, data={}, motor='odoo'):
        '''
        :param api:
        :param data: objeto con la data que se desea enviar a la api
        :param motor: por defecto odoo
        :return:
        '''

        if motor != 'odoo':
            raise NotImplementedError
        conf = SERVICE.get(motor, None)
        if not data:
            raise Exception('Data es un argumento obligatorio para POST')
        if not api:
            raise Exception('Api es un argumento obligatorio')
        if not api.startswith('/'):
            api = '/%s' % api
        if not conf:
            raise Exception('Motor %s no esta configurado para este ambiente'%motor)

        url = '%(protocol)s://%(host)s:%(port)s' % conf
        header = conf.get('header', None)
        #data = conf.get('default_data', None)
        try:
            data = json.dumps(data)
        except:
            pass

        if conf['auth']:
            auth_service = conf['auth']
            #si la api requiere que este autenticado
            method = auth_service['method']()

            session_id = redis_cnx.get('session_id')

            if not session_id:
                session_id = self.login(url=url + auth_service['api'], data=auth_service['credentials'], headers=header,
                                        service=method)
                result = redis_cnx.setex('session_id',TTL , session_id)
                if not result:
                    pass
                    #result

            cookie = requests.cookies.create_cookie(name='session_id', value=str(session_id))
            # method.cookies['session_id'] = session_id
            method.cookies.set_cookie(cookie)

            response = method.post(url+api, data=data, verify=conf['ssl_check'], headers=header)
        else:
            response = requests.post(url+api, data=data, auth=conf['auth'], verify=conf['ssl_check'], headers=header)

        if response.status_code is not 201:
            return response.text
        return response.json()

    def get(self, api=None, motor='odoo'):
        '''
        :param api: en formato /api/../../..
        :param motor:
            'odoo' -> para api escritas en odoo
            'graphql' -> para api disponible en graphql
        :return: requests.get()
        '''
        conf = SERVICE.get(motor, None)
        #conf = {
        #    'host': 'apps.galilea.cl',
        #    'protocol': 'http',
        #    'port': '8069'
        #},
        if motor != 'odoo':
            raise NotImplementedError
        if not api:
            raise Exception('Api es un argumento obligatorio')
        if not api.startswith('/'):
            api = '/%s' % api
        if not conf:
            raise Exception('Motor %s no esta configurado para este ambiente'%motor)

        header = conf.get('header', None)
        url = '%(protocol)s://%(host)s:%(port)s' % conf

        data = conf.get('default_data', None)

        if conf['auth']:
            auth_service = conf['auth']
            #si la api requiere que este autenticado
            method = auth_service['method']()

            session_id = redis_cnx.get('session_id')

            if not session_id:
                session_id = self.login(url=url + auth_service['api'], data=auth_service['credentials'], headers=header, service=method)
                result = redis_cnx.setex('session_id', TTL, session_id)
                if not result:
                    pass
                    #result

            cookie = requests.cookies.create_cookie(name='session_id', value=str(session_id))
            #method.cookies['session_id'] = session_id
            method.cookies.set_cookie(cookie)

            response = method.get(url+api, data=data, verify=conf['ssl_check'], headers=header)
        else:
            response = requests.get(url+api, data=data, verify=conf['ssl_check'], headers=header)
        if response.status_code is not 200:
            return response.text
        #TODO: hacer parser de la respuesta por motor, para obtener siempre un response limpio
        return response.json()


if __name__ == '__main__':
    api = ApiRequest()
    result = api.get('url/to/test/1', motor='odoo')
    print (result)
    result = api.get('url/to/test/2', motor='graphql')
    print (result)

