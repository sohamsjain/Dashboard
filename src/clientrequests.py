import requests

from src.constants import HOST
PORT = 5000
baseurl = f"http://{HOST}:{PORT}"
xoneendpoint = f"{baseurl}/xones"
childendpoint = f"{baseurl}/children"


class XoneRequests:

    @staticmethod
    def get(**kwargs):
        response = requests.get(xoneendpoint, params=kwargs)
        return response.json()

    @staticmethod
    def create(**kwargs):
        response = requests.post(xoneendpoint, json=kwargs)
        return response.json()

    @staticmethod
    def update(**kwargs):
        response = requests.put(xoneendpoint, json=kwargs)
        return response.json()

    @staticmethod
    def delete(**kwargs):
        response = requests.delete(xoneendpoint, json=kwargs)
        return response.json()


class ChildRequests:
    endpoint = "/children"

    @staticmethod
    def get(**kwargs):
        response = requests.get(childendpoint, params=kwargs)
        return response.json()

    @staticmethod
    def create(**kwargs):
        response = requests.post(childendpoint, json=kwargs)
        return response.json()

    @staticmethod
    def update(**kwargs):
        response = requests.put(childendpoint, json=kwargs)
        return response.json()

    @staticmethod
    def delete(**kwargs):
        response = requests.delete(childendpoint, json=kwargs)
        return response.json()
