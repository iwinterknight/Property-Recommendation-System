def create_numeric_atomic(attribute, exact, range, lrange, urange, val, lval, rval):
    atomic_query = None
    if exact:
        atomic_query = {
            "query": {
                "match": {
                    attribute: val,
                }
            }
        }
    elif range:
        atomic_query = {
            "query": {
                "range": {
                    attribute: {"gte": lval, "lte": rval}
                }
            }
        }
    elif lrange:
        atomic_query = {
            "query": {
                "range": {
                    attribute: {"gte": lval}
                }
            }
        }
    elif urange:
        atomic_query = {
            "query": {
                "range": {
                    attribute: {"lte": rval}
                }
            }
        }

    return atomic_query


def create_text_atomic(attribute, phrase, approx, boost=1.0):
    if approx:
        atomic_query = {
            "query": {
                "match": {
                    attribute: {
                        "query": phrase,
                        "boost": boost,
                        "fuzziness": 2,
                        "prefix_length": 0,
                        "max_expansions": 100
                    }
                }
            }
        }
    else:
        atomic_query = {
            "query": {
                "match": {
                    attribute: {
                        "query": phrase,
                    }
                }
            }
        }
    return atomic_query


def form_query(attribute_form):
    query = {"bool": {"must": [], "must_not": []}}
    for i, attribute in enumerate(attribute_form):
        atomic_query = None
        if attribute["numeric"]:
            atomic_query = create_numeric_atomic(attribute["attribute"], attribute["exact"], attribute["range"],
                                                 attribute["lrange"], attribute["urange"], attribute["val"],
                                                 attribute["lval"], attribute["rval"])
        elif attribute["text"]:
            atomic_query = create_text_atomic(attribute["attribute"], attribute["phrase"], attribute["approx"],
                                              attribute["boost"])
        if attribute["negate"]:
            query_list = query["bool"]["must_not"]
            query_list.append(atomic_query["query"])
        else:
            query_list = query["bool"]["must"]
            query_list.append(atomic_query["query"])

    return query


def create_elasticsearch_query(completed_dialog_state):
    query = {"bool": {"should": [], "must": [], "must_not": []}}

    numeric_attributes = ['lq_bedrooms', 'lq_bathrooms', 'lq_area', 'lq_price', 'lq_schools_rating', 'lq_house_age']
    text_attributes = ['lq_house_flooring', 'lq_sea_proximity', 'lq_house_public_transport', 'lq_neighborhood_features']
    for state_key, state_value in completed_dialog_state.items():
        if state_key == "lq_school_rating":
            state_key = "lq_schools_rating"

        description = state_value["_description"]
        if description == "RESPONSE":
            if state_key in numeric_attributes:
                attribute = state_key[3:]
                exact = True
                val = state_value["_input"]
                range = False
                lrange = False
                urange = False
                lval = None
                rval = None
                atomic_query = create_numeric_atomic(attribute, exact, range, lrange, urange, val, lval, rval)
            elif state_key in text_attributes:
                attribute = state_key[3:]
                val = state_value["_input"]
                approx = False
                boost = 1.0
                atomic_query = create_text_atomic(attribute, val, approx, boost)
        elif description == "RANGE":
            if state_key in numeric_attributes:
                attribute = state_key[3:]
                exact = False
                val = None
                range_val = state_value["_input"]
                if len(range_val) == 2:
                    range = True
                    lrange = False
                    urange = False
                    lval = range_val["greater_than"]
                    rval = range_val["less_than"]
                    atomic_query = create_numeric_atomic(attribute, exact, range, lrange, urange, val, lval, rval)
                elif len(range_val) == 1:
                    range = False
                    if "greater_than" in range_val:
                        lrange = True
                        urange = False
                        lval = range_val["greater_than"]
                        rval = None
                        atomic_query = create_numeric_atomic(attribute, exact, range, lrange, urange, val, lval, rval)
                    elif "less_than" in range_val:
                        lrange = False
                        urange = True
                        lval = None
                        rval = range_val["less_than"]
                        atomic_query = create_numeric_atomic(attribute, exact, range, lrange, urange, val, lval, rval)
        if state_key in ['lq_bedrooms', 'lq_bathrooms', 'lq_area', 'lq_price']:
            query_list = query["bool"]["must"]
        else:
            query_list = query["bool"]["should"]

        # if state_key in ['lq_house_flooring', 'lq_schools_rating']:
        #     if 'match' in atomic_query['query']:
        #         atomic_query['query']['match']['boost'] = 5.0
        #     elif 'range' in atomic_query['query']:
        #         atomic_query['query']['range']['boost'] = 5.0
        query_list.append(atomic_query["query"])

    return query
