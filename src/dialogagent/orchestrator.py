import pickle
import random
import uuid
from src.dialogagent.dialog_agent_prompts import prompts
from nlu.nlu_utils import extract_intents_slots, get_closest_sentence
from src.dialogagent.llm_prompts import get_llm_response, generate_paraphrase
from src.elasticsearch.elasticsearch_manager import ElasticSearchManager
from src.elasticsearch.execute_elasticsearch import index_data
from src.elasticsearch.execute_elasticsearch import search_index

CRED = '\033[91m'
CGREEN = '\33[32m'
CYELLOW = '\33[33m'
CEND = '\033[0m'


class DialogAgent:
    def __init__(self):
        self.dialog_states = ["lq_bedrooms", "lq_bathrooms", "lq_area", "lq_price", "lq_house_flooring", "lq_house_age",
                              "lq_sea_proximity", "lq_school_rating", "lq_house_public_transport",
                              "lq_neighborhood_features"]
        self.dialog_states_to_nl = {"lq_bedrooms": "number of bedrooms", "lq_bathrooms": "number of bathrooms",
                                    "lq_area": "area of the house", "lq_price": "price of the house",
                                    "lq_house_flooring": "flooring type in the house",
                                    "lq_house_age": "age of the house",
                                    "lq_sea_proximity": "house's proximity to the sea",
                                    "lq_school_rating": "school district rating of the house location",
                                    "lq_house_public_transport": "public transport options accessible from the house",
                                    "lq_neighborhood_features": "amenities offered by the locality of the house"}
        self.intents = ["lead_qualification", "OOD"]
        self.required_states = ["lq_bedrooms", "lq_bathrooms", "lq_price"]
        self.current_state_ctr = None
        self.total_states = None
        self.response_generation = []
        self.state_parameter_dicts = {}
        self.state_history = []
        self.response_prefix_dict = {}

    def initialize_dialog_agent(self):
        self.current_state_ctr = 0
        self.total_states = len(self.dialog_states)
        for state in self.dialog_states:
            state_dict = {}
            if state in self.required_states:
                state_dict["required"] = True
            else:
                state_dict["required"] = False
            state_dict["prompts"] = prompts[state]
            state_dict["_input"] = None
            state_dict["_description"] = None
            self.state_parameter_dicts[state] = state_dict

    def start_dialogue(self):
        introduction_msg = random.sample(prompts["introduction"], 1)[0]
        return introduction_msg

    def get_llm_numeric_response(self, state, user_msg, response_prefix_dict):
        response_status, response = get_llm_response(state, user_msg, state_history=[], OOD=False)
        if response_status == "ERROR":
            response_prefix_dict[state] = ("ERROR", None)
            return
        if response_status == "RESPONSE":
            llm_dialog_state = self.state_parameter_dicts[state]
            if not llm_dialog_state["_input"]:
                if state == "lq_price":
                    adjusted_response = response * 10
                    llm_dialog_state["_input"] = int(adjusted_response)
                else:
                    llm_dialog_state["_input"] = int(response)
                llm_dialog_state["_description"] = response_status
                response_prefix_dict[state] = ("RESPONSE", int(response))
        elif response_status == "RANGE":
            llm_dialog_state = self.state_parameter_dicts[state]
            if not llm_dialog_state["_input"]:
                llm_dialog_state["_description"] = response_status
                if state == "lq_price":
                    adjusted_response = {}
                    if "less_than" in response:
                        adjusted_response["less_than"] = response["less_than"] * 10
                    if "greater_than" in response:
                        adjusted_response["greater_than"] = response["greater_than"] * 10
                    llm_dialog_state["_input"] = adjusted_response
                else:
                    llm_dialog_state["_input"] = response
                response_prefix_dict[state] = ("RANGE", response)

    def run_dialog_flow(self):
        state_msg = ""
        response_prefix_dict = {}
        while self.current_state_ctr < self.total_states:
            current_state = self.dialog_states[self.current_state_ctr]
            current_state_dict = self.state_parameter_dicts[current_state]

            prefix_prompt = ""
            for state_key, state_value in response_prefix_dict.items():
                if state_key == "lq_sea_proximity":
                    continue
                state_key_nl = self.dialog_states_to_nl[state_key]
                state_response_type = state_value[0]
                v = state_value[1]
                if state_response_type == "RANGE":
                    if "less_than" in v and "greater_than" in v:
                        v_lt = v["less_than"]
                        v_gt = v["greater_than"]
                        prefix_prompt += "Awesome! You listed your requirement for " + state_key_nl + " ranging between " + str(
                            v_lt) + " and " + str(v_gt)
                    elif "less_than" in v:
                        v_lt = v["less_than"]
                        prefix_prompt += "Awesome! You listed your requirement for " + state_key_nl + "  as less than " + str(
                            v_lt)
                    elif "greater_than" in v:
                        v_gt = v["greater_than"]
                        prefix_prompt += "Awesome! You listed your requirement for " + state_key_nl + "  to greater than " + str(
                            v_gt)
                    prefix_prompt += "\nNow let's get some more requirements.\n"
                elif state_response_type == "RESPONSE":
                    prefix_prompt += "Great! You listed your requirement for " + state_key_nl + " as " + str(v)
                    prefix_prompt += "\nNow let's get some more requirements.\n"
                elif state_response_type == "ERROR":
                    prefix_prompt += "Oops! I'm sorry it seems I couldn't catch what you specified for " + state_key_nl + ". Maybe try stating your requirement values explicitly."
                    prefix_prompt += "\nLet's try that again..\n"

            state_msg = random.sample(current_state_dict["prompts"], 1)[0]

            if len(response_prefix_dict) > 0 and prefix_prompt:
                paraphrased_prefix_prompt = generate_paraphrase(prefix_prompt)
                if paraphrased_prefix_prompt and "-1" not in paraphrased_prefix_prompt:
                    state_msg = paraphrased_prefix_prompt + "\n" + state_msg

        return state_msg

    def execute_turn(self, user_msg, first_turn=False):
        if not first_turn:
            previous_state = self.dialog_states[self.current_state_ctr]
            self.execute_nlu(self.dialog_states[self.current_state_ctr], user_msg, self.response_prefix_dict)

        if self.current_state_ctr == self.total_states:
            state_msg = generate_paraphrase(
                "Thanks! Now that I have all your requirements let me fetch some options for you.")
            return state_msg

        if self.current_state_ctr < self.total_states:
            current_state = self.dialog_states[self.current_state_ctr]
            current_state_dict = self.state_parameter_dicts[current_state]
            state_msg = random.sample(current_state_dict["prompts"], 1)[0]
            if not first_turn:
                prefix_prompt = ""
                for state_key, state_value in self.response_prefix_dict.items():
                    if state_key == previous_state:
                        if state_key == "lq_sea_proximity":
                            continue
                        state_key_nl = self.dialog_states_to_nl[state_key]
                        state_response_type = state_value[0]
                        v = state_value[1]
                        if state_response_type == "RANGE":
                            if "less_than" in v and "greater_than" in v:
                                v_lt = v["less_than"]
                                v_gt = v["greater_than"]
                                prefix_prompt += "Awesome! You listed your requirement for " + state_key_nl + " ranging between " + str(
                                    v_lt) + " and " + str(v_gt)
                            elif "less_than" in v:
                                v_lt = v["less_than"]
                                prefix_prompt += "Awesome! You listed your requirement for " + state_key_nl + "  as less than " + str(
                                    v_lt)
                            elif "greater_than" in v:
                                v_gt = v["greater_than"]
                                prefix_prompt += "Awesome! You listed your requirement for " + state_key_nl + "  to greater than " + str(
                                    v_gt)
                            prefix_prompt += "\nNow let's get some more requirements.\n"
                        elif state_response_type == "RESPONSE":
                            prefix_prompt += "Great! You listed your requirement for " + state_key_nl + " as " + str(v)
                            prefix_prompt += "\nNow let's get some more requirements.\n"
                        elif state_response_type == "ERROR":
                            prefix_prompt += "Oops! I'm sorry it seems I couldn't catch what you specified for " + state_key_nl + ". Maybe try stating your requirement values explicitly."
                            prefix_prompt += "\nLet's try that again..\n"

                if len(self.response_prefix_dict) > 0 and prefix_prompt:
                    paraphrased_prefix_prompt = generate_paraphrase(prefix_prompt)
                    if paraphrased_prefix_prompt and "-1" not in paraphrased_prefix_prompt:
                        state_msg = paraphrased_prefix_prompt + "\n" + state_msg
            return state_msg

    def run_dialog_flow(self):
        previous_state_ctr = 0
        self.response_prefix_dict = {}
        while self.current_state_ctr < self.total_states:
            # if self.current_state_ctr > 0 and self.current_state_ctr == previous_state_ctr:
            # current_state_dict = prompts["invalid_response"]
            # next_step_prompt = random.sample(current_state_dict["prompts"], 1)[0]
            # print(next_step_prompt)

            current_state = self.dialog_states[self.current_state_ctr]
            current_state_dict = self.state_parameter_dicts[current_state]

            prefix_prompt = ""
            for state_key, state_value in self.response_prefix_dict.items():
                if state_key == "lq_sea_proximity":
                    continue
                state_key_nl = self.dialog_states_to_nl[state_key]
                state_response_type = state_value[0]
                v = state_value[1]
                if state_response_type == "RANGE":
                    if "less_than" in v and "greater_than" in v:
                        v_lt = v["less_than"]
                        v_gt = v["greater_than"]
                        prefix_prompt += "Awesome! You listed your requirement for " + state_key_nl + " ranging between " + str(
                            v_lt) + " and " + str(v_gt)
                    elif "less_than" in v:
                        v_lt = v["less_than"]
                        prefix_prompt += "Awesome! You listed your requirement for " + state_key_nl + "  as less than " + str(
                            v_lt)
                    elif "greater_than" in v:
                        v_gt = v["greater_than"]
                        prefix_prompt += "Awesome! You listed your requirement for " + state_key_nl + "  to greater than " + str(
                            v_gt)
                    prefix_prompt += "\nNow let's get some more requirements.\n"
                elif state_response_type == "RESPONSE":
                    prefix_prompt += "Great! You listed your requirement for " + state_key_nl + " as " + str(v)
                    prefix_prompt += "\nNow let's get some more requirements.\n"
                elif state_response_type == "ERROR":
                    prefix_prompt += "Oops! I'm sorry it seems I couldn't catch what you specified for " + state_key_nl + ". Maybe try stating your requirement values explicitly."
                    prefix_prompt += "\nLet's try that again..\n"

            state_msg = random.sample(current_state_dict["prompts"], 1)[0]

            if len(self.response_prefix_dict) > 0 and prefix_prompt:
                paraphrased_prefix_prompt = generate_paraphrase(prefix_prompt)
                if paraphrased_prefix_prompt and "-1" not in paraphrased_prefix_prompt:
                    print(CGREEN + paraphrased_prefix_prompt + CEND)

            user_msg = input(CYELLOW + "\n{}".format(state_msg) + CEND)

            previous_state_ctr = self.current_state_ctr
            response_prefix_dict = {}
            self.execute_nlu(self.dialog_states[self.current_state_ctr], user_msg, response_prefix_dict)

        lq_complete_prompt = generate_paraphrase(
            "Thanks! Now that I have all your requirements let me fetch some options for you.")
        print(CRED + lq_complete_prompt + CEND)

        return self.state_parameter_dicts

    def execute_nlu(self, state, user_msg, response_prefix_dict):
        tagged_entity_dialog_state = self.state_parameter_dicts[state]
        if tagged_entity_dialog_state["_input"]:
            self.current_state_ctr += 1
            return

        if state in self.required_states:
            tagged_intents_slots = extract_intents_slots(user_msg, "lead_qualification")
            intent = tagged_intents_slots["intent"]
            if intent is not None and intent == "findApartmentBedBathCityPrice":
                if "num_bedrooms" in tagged_intents_slots:
                    tagged_entity_num_bedrooms = tagged_intents_slots["num_bedrooms"]
                    tagged_entity_dialog_state = self.state_parameter_dicts["lq_bedrooms"]
                    if not tagged_entity_dialog_state["_input"]:
                        tagged_entity_dialog_state["_input"] = tagged_entity_num_bedrooms
                        tagged_entity_dialog_state["_description"] = "RESPONSE"
                        response_prefix_dict["lq_bedrooms"] = ("RESPONSE", tagged_entity_num_bedrooms)

                if "num_bathrooms" in tagged_intents_slots:
                    tagged_entity_num_bathrooms = tagged_intents_slots["num_bathrooms"]
                    tagged_entity_dialog_state = self.state_parameter_dicts["lq_bathrooms"]
                    if not tagged_entity_dialog_state["_input"]:
                        tagged_entity_dialog_state["_input"] = tagged_entity_num_bathrooms
                        tagged_entity_dialog_state["_description"] = "RESPONSE"
                        response_prefix_dict["lq_bathrooms"] = ("RESPONSE", tagged_entity_num_bathrooms)

                if "price" in tagged_intents_slots:
                    tagged_entity_price = tagged_intents_slots["price"]
                    tagged_entity_price *= 10
                    tagged_entity_dialog_state = self.state_parameter_dicts["lq_price"]
                    if not tagged_entity_dialog_state["_input"]:
                        tagged_entity_dialog_state["_input"] = tagged_entity_price
                        tagged_entity_dialog_state["_description"] = "RESPONSE"
                        response_prefix_dict["lq_price"] = ("RESPONSE", tagged_entity_price)

        if state in ["lq_bedrooms", "lq_bathrooms", "lq_price"]:
            tagged_entity_dialog_state = self.state_parameter_dicts[state]
            if not tagged_entity_dialog_state["_input"]:
                self.get_llm_numeric_response(state, user_msg, response_prefix_dict)
                if response_prefix_dict[state][0] == "ERROR":
                    return
        if state in ["lq_area", "lq_house_age", "lq_school_rating"]:
            self.get_llm_numeric_response(state, user_msg, response_prefix_dict)
            if response_prefix_dict[state][0] == "ERROR":
                return
        elif state == "lq_house_flooring":
            response_status, response = get_llm_response(state, user_msg, state_history=[], OOD=False)
            if response_status == "ERROR":
                response_prefix_dict[state] = ("ERROR", None)
                return
            llm_dialog_state = self.state_parameter_dicts[state]
            if not llm_dialog_state["_input"]:
                if response_status == "RESPONSE":
                    llm_dialog_state["_input"] = response
                    llm_dialog_state["_description"] = "RESPONSE"
                    response_prefix_dict[state] = ("RESPONSE", response)
                elif response_status == "ERROR":
                    # llm_dialog_state["_input"] = user_msg
                    response_prefix_dict[state] = ("ERROR", None)
                    return
        elif state == "lq_sea_proximity":
            # response_status, response = get_llm_response(state, user_msg, state_history=[], OOD=False)
            # if response_status == "ERROR":
            #     return
            response_status = "RESPONSE"
            response = get_closest_sentence(user_msg, ["seaside", "less than hour to sea", "inland", "by the sea",
                                                       "far from sea"])
            filtered_response = None
            llm_dialog_state = self.state_parameter_dicts[state]
            if not llm_dialog_state["_input"]:
                if response_status == "RESPONSE":
                    if response == "seaside" or response == "by the sea":
                        filtered_response = "NEAR OCEAN, ISLAND"
                    elif response == "less than hour to sea":
                        filtered_response = "NEAR BAY, 1H OCEAN"
                    elif response == "inland" or response == "far from sea":
                        filtered_response = "INLAND"
                    llm_dialog_state["_input"] = filtered_response
                    llm_dialog_state["_description"] = "RESPONSE"
                    response_prefix_dict[state] = ("RESPONSE", filtered_response)
                elif response_status == "ERROR":
                    # llm_dialog_state["_input"] = user_msg
                    response_prefix_dict[state] = ("ERROR", None)
                    return
        elif state == "lq_house_public_transport":
            # response_status, response = get_llm_response(state, user_msg, state_history=[], OOD=False)
            # if response_status == "ERROR":
            #     return
            response_status = "RESPONSE"
            response = get_closest_sentence(user_msg, ["bus", "subway"])
            filtered_response = None
            llm_dialog_state = self.state_parameter_dicts[state]
            if not llm_dialog_state["_input"]:
                if response_status == "RESPONSE":
                    if response == "bus":
                        filtered_response = "Bus Stop"
                    elif response == "subway":
                        filtered_response = "Subway"
                    llm_dialog_state["_input"] = filtered_response
                    llm_dialog_state["_description"] = "RESPONSE"
                    response_prefix_dict[state] = ("RESPONSE", filtered_response)
                elif response_status == "ERROR":
                    # llm_dialog_state["_input"] = user_msg
                    response_prefix_dict[state] = ("ERROR", None)
                    return
        elif state == "lq_neighborhood_features":
            llm_dialog_state = self.state_parameter_dicts[state]
            if not llm_dialog_state["_input"]:
                llm_dialog_state["_input"] = user_msg
                llm_dialog_state["_description"] = "RESPONSE"

        if state in self.required_states:
            dialog_state = self.state_parameter_dicts[state]
            if not dialog_state["_input"]:
                pass
            else:
                self.current_state_ctr += 1
        else:
            self.current_state_ctr += 1
        return


def setup_recommendation_system():
    es_manager = ElasticSearchManager()
    index_uuid = str(uuid.uuid4())
    index_data(es_manager, index_name=index_uuid)
    with open("ElasticIndexName", "w") as f:
        f.write(index_uuid)

    dialogagent = DialogAgent()
    dialogagent.initialize_dialog_agent()
    dialogagent.start_dialogue()

    with open("ElasticIndexName", "r") as f:
        index_uuid = f.read()
    es_manager.setup_search_client(index_name=index_uuid)
    return es_manager, dialogagent


def generate_recommendations(es_manager, dialog_state):
    return search_index(es_manager, dialog_state)


def main():
    es_manager = ElasticSearchManager()
    # index_uuid = str(uuid.uuid4())
    # index_data(es_manager, index_name=index_uuid)
    # with open("ElasticIndexName", "w") as f:
    #     f.write(index_uuid)

    agent = DialogAgent()
    agent.initialize_dialog_agent()
    agent.start_dialogue()
    # completed_dialog_state = agent.run_dialog_flow()

    with open("completed_dialog_state.pkl", "rb") as f:
        completed_dialog_state = pickle.load(f)

    completed_dialog_state["lq_price"]["_input"] = {"less_than": 19000000}
    # completed_dialog_state["lq_sea_proximity"]["_input"] = "INLAND"

    with open("ElasticIndexName", "r") as f:
        index_uuid = f.read()
    es_manager.setup_search_client(index_name=index_uuid)
    search_index(es_manager, completed_dialog_state)
    print("Fin!")


if __name__ == '__main__':
    main()
