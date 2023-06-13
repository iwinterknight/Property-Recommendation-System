from flask import Flask, request, jsonify
from nlu.nlu_utils import extract_intents_slots

app = Flask(__name__)


@app.route("/nlu", methods=["POST", "GET"])
def nlu():
    query = request.args['query']
    intent = request.args['intent']

    output = extract_intents_slots(query, intent)
    return jsonify(output)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port="8000", debug=False)