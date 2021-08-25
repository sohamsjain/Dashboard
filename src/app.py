from flask import Flask
from flask_restful import Resource, Api, reqparse
from src.BaTMan import BaTMan

app = Flask(__name__)
api = Api(app)
bat = BaTMan()


class Xones(Resource):

    def get(self):
        pass

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("symbol", type=str, required=True)
        parser.add_argument("entry", type=float, required=True)
        parser.add_argument("stoploss", type=float, required=True)
        parser.add_argument("target", type=float, required=True)
        parser.add_argument("children", type=list, required=True, location='json')
        args = parser.parse_args()
        response = bat.createxone(args)
        return response, 200

    def put(self):
        pass

    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument("xone_id", type=int, required=True)
        args = parser.parse_args()
        response = bat.deletexone(args["xone_id"])
        return response, 200


class Children(Resource):

    def get(self):
        return "success", 200

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("xone_id", type=int, required=True)
        parser.add_argument("symbol", type=str, required=True)
        parser.add_argument("size", type=int, required=True)
        args = parser.parse_args()
        response = bat.createchild(args)
        return response, 200

    def put(self):
        pass

    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument("child_id", type=int, required=True)
        args = parser.parse_args()
        response = bat.deletechild(args["child_id"])
        return response, 200


api.add_resource(Xones, '/xones')
api.add_resource(Children, '/children')

if __name__ == '__main__':
    app.run(host="0.0.0.0")
