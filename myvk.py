import urllib
import json
API_TEMPLATE = "https://api.vk.com/method/{}.{}?{}&access_token={}"


class Photos():
    def __init__(self, token):
        self.token = token
        self.template = API_TEMPLATE.format("photos", "{}", "{}", "{}")

    def __getattr__(self, name):
        def wrapper(*args, **kwargs):
            print "'%s' was called" % name
        return wrapper


class VKMethod():
    def __init__(self, method, token):
        self.method = method
        self.token = token

    def __getattr__(self, func):

        def wrapper(*args, **kwargs):
            params = ""
            for k, v in kwargs.items():
                params += "{}={}&".format(k, v)
            params += 'v=5.21'
            data = urllib.urlopen(API_TEMPLATE.format(self.method, func, params, self.token))

            js = json.load(data)
            return js['response']
        return wrapper

    def __str__(self):
        return "lol"


class Api():
    def __init__(self, token, appID):
        self.token = token
        self.appID = appID

    def __getattr__(self, name):
        method = VKMethod(name, self.token)
        setattr(self, name, method)
        return method







