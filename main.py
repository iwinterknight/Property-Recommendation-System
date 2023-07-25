import pickle

from flask import Flask, request, jsonify

# from nlu.nlu_utils import extract_intents_slots
from src.dialogagent.orchestrator import setup_recommendation_system, generate_recommendations
from nlu.nlu_utils import get_closest_sentence
app = Flask(__name__)

es_manager, dialog_agent = setup_recommendation_system()
TOTAL_TURNS = dialog_agent.total_states
turn_ctr = 0


# @app.route("/nlu", methods=["POST", "GET"])
# def nlu():
#     query = request.args['query']
#     intent = request.args['intent']
#
#     output = extract_intents_slots(query, intent)
#     return jsonify(output)


@app.route("/run_dialog_flow", methods=["POST", "GET"])
def run_dialog_flow():
    request_obj = request.get_json(force=True)
    user_msg = request_obj.get("message")
    global turn_ctr
    if turn_ctr == 0:
        bot_response = dialog_agent.execute_turn(user_msg=user_msg, first_turn=True)
    else:
        bot_response = dialog_agent.execute_turn(user_msg=user_msg, first_turn=False)
    turn_ctr = turn_ctr + 1
    return jsonify(bot_response)


@app.route("/fetch_recommendations", methods=["POST", "GET"])
def fetch_recommendations():
    # with open("complete_state_parameters_dict.pkl", "rb") as f:
    #     loaded_state_parameter_dicts = pickle.load(f)
    # recommendations = generate_recommendations(es_manager, loaded_state_parameter_dicts)
    recommendations = generate_recommendations(es_manager, dialog_agent.state_parameter_dicts)
    return jsonify(recommendations)


@app.route("/classify_intent", methods=["POST", "GET"])
def classify_intent():
    request_obj = request.get_json(force=True)
    user_msg = request_obj.get("message")
    response = get_closest_sentence(user_msg, ["housing", "music"])
    return jsonify(response)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8090)
