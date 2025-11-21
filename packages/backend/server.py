from flask import Flask

from packages.shared.sharedConstants import WebServerHost, WebServerPort
from packages.shared.types.networkTypes import makeResponse

app = Flask(__name__)

@app.route("/ping", methods=["GET"])
def ping():
  return makeResponse(success=True, message="Pong!", content=None)

@app.route("/events/add", methods=["POST"])
def add_event():
    # TODO
    return makeResponse(success=True, message="Event added successfully", content=None)

@app.route("/events/get", methods=["GET"])
def get_events():
    # TODO
    return makeResponse(success=True, message="Events retrieved successfully", content=None)


@app.route("/rules/add", methods=["POST"])
def add_rule():
    # TODO
    return makeResponse(success=True, message="Rule added successfully", content=None)

@app.route("/rules/get", methods=["GET"])
def get_rules():
    # TODO
    return makeResponse(success=True, message="Rules retrieved successfully", content=None)

@app.route("/manage/recalculate", methods=["POST"])
def recalculate():
    # TODO
    return makeResponse(success=True, message="Recalculation completed successfully", content=None)


if __name__ == "__main__":
  app.run(host=WebServerHost, port=WebServerPort, debug=True)