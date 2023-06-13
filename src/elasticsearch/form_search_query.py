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


def create_text_atomic(attribute, phrase, approx, boost):
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


def create_attribute_form(completed_dialog_state):
    for state_key, state_value in completed_dialog_state.items():
