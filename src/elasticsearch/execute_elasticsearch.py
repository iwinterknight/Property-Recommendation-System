from elasticsearch_manager import ElasticSearchManager
from form_search_query import form_query
from data.mappings import housing_features_mapping


def index_data(es_manager):
    index_name = "housing_features"
    index_mapping = housing_features_mapping
    data_path = "../../data/housing_features.csv"
    es_manager.create_es_index(index_name=index_name, index_mapping=index_mapping, data_path=data_path)
    es_manager.setup_search_client(index_name=index_name)


def search_index(es_manager, attribute_form):
    index_name = "housing_features"
    query = form_query(attribute_form)
    res = es_manager.search_index(query, index_name)
    print("Got %d Hits:" % res['hits']['total']['value'])
    for i, hit in enumerate(res['hits']['hits']):
        print("Result {} : {}\tScore : {}".format(i, hit["_source"], hit["_score"]))


sample_query = {
    "bool": {
        "must": [
            {
                "match": {
                    "house_flooring": "linoleum",
                }
            },

            {
                "match": {
                    "neighborhood_features": {
                        "query": "Cafe, Diner, Recreation",
                        "boost": 1.0,
                        "fuzziness": 2,
                        "prefix_length": 0,
                        "max_expansions": 100
                    }
                }
            },

            {
                "range": {
                    "bedrooms": {"gte": 1, "lte": 2}
                },
            },

            {
                "range": {
                    "bathrooms": {"gte": 1, "lte": 2}
                }
            }
        ],
    }
}

attribute_form = [
    {
        "numeric": True,
        "text": False,
        "negate": False,
        "attribute": "bedrooms",
        "exact": True,
        "range": False,
        "lrange": False,
        "urange": False,
        "val": 3,
        "lval": None,
        "rval": None
    },
    {
        "numeric": True,
        "text": False,
        "negate": False,
        "attribute": "bathrooms",
        "exact": False,
        "range": True,
        "lrange": False,
        "urange": False,
        "val": None,
        "lval": 2,
        "rval": 3
    },
    {
        "numeric": True,
        "text": False,
        "negate": False,
        "attribute": "price",
        "exact": False,
        "range": False,
        "lrange": False,
        "urange": True,
        "val": None,
        "lval": None,
        "rval": 8500000
    },
    {
        "numeric": False,
        "text": True,
        "attribute": "neighborhood_features",
        "match": True,
        "negate": False,
        # "phrase": "Swimming Pool, Gym, Activity Center",
        "phrase": "Diner",
        "approx": True,
        "boost": 2.0
    },
    {
        "numeric": False,
        "text": True,
        "attribute": "house_flooring",
        "match": False,
        "negate": True,
        "phrase": "linoleum",
        "approx": True,
        "boost": 1.0
    }
]


es_manager = ElasticSearchManager()
es_manager.setup_search_client(index_name="housing_features")
search_index(es_manager, attribute_form)