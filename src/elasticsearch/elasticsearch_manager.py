import json
import os
from src.elasticsearch.elasticsearch_service import EsManagement


class ElasticSearchManager:
    def __init__(self):
        self.es_connection = EsManagement()
        self.es_client = None

    def create_es_index(self, index_name, index_mapping, data_path):
        self.es_connection.create_index(index_name=index_name, mapping=index_mapping)

        # print(
        #     json.dumps(
        #         self.es_connection.es_client.indices.get_mapping(index=index_name).body,
        #         indent=1)
        # )

        self.es_connection.populate_index(index_name=index_name,
                                     path=data_path)
        print(self.es_connection.es_client.count(index=index_name))

    def setup_search_client(self, index_name):
        self.es_client = self.es_connection.es_client
        self.es_client.indices.refresh(index=index_name)
        print(self.es_client.cat.count(index=index_name, format="json"))

    def search_index(self, query, index_name):
        res = self.es_client.search(index=index_name, body={"query" : query})
        return res