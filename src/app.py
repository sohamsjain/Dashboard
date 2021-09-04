from flask import Flask
from flask_restful import Resource, Api, reqparse
from src.BaTMan import BaTMan
from src.util import ChildType

app = Flask(__name__)
api = Api(app)
bat = BaTMan()


class Xones(Resource):

    def get(self):
        return "success", 200

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("symbol", type=str, required=True)
        parser.add_argument("entry", type=float, required=True)
        parser.add_argument("stoploss", type=float, required=True)
        parser.add_argument("target", type=float, required=True)
        parser.add_argument("children", type=list, required=False, location='json')
        parser.add_argument("autonomous", type=bool, required=False)
        args = parser.parse_args()
        response = bat.createxone(args)
        return response, 200

    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument("xone_id", type=int, required=True)
        parser.add_argument("entry", type=float, required=False)
        parser.add_argument("stoploss", type=float, required=False)
        parser.add_argument("target", type=float, required=False)
        parser.add_argument("autonomous", type=bool, required=False)
        parser.add_argument("forced_entry", type=bool, required=False)
        parser.add_argument("forced_exit", type=bool, required=False)
        args = parser.parse_args()
        response = bat.updatexone(args)
        return response, 200

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
        parser.add_argument("type", type=str, required=False, choices=(ChildType.SELL, ChildType.BUY))
        args = parser.parse_args()
        response = bat.createchild(args)
        return response, 200

    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument("child_id", type=int, required=True)
        parser.add_argument("size", type=int, required=False)
        args = parser.parse_args()
        response = bat.updatechild(args)
        return response, 200

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
