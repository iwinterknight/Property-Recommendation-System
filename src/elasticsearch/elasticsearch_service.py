import json
import logging
import csv
from elasticsearch.helpers import bulk

from typing import Dict

import numpy as np
import pandas as pd
from elasticsearch import Elasticsearch

logging.basicConfig(filename="es.log", level=logging.INFO)


class EsManagement:
    def __init__(self):
        self.es_client = Elasticsearch(
            hosts="http://localhost:9200",
            # basic_auth=(USER, PASS), verify_certs=False
            # [os.environ["HOST"]],
            # http_auth=(os.environ["ACCESS_KEY"], os.environ["ACCESS_SECRET"])
        )
        logging.info(self.es_client.ping())

    def create_index(self, index_name: str, mapping: Dict) -> None:
        """
        Create an ES index.
        :param index_name: Name of the index.
        :param mapping: Mapping of the index
        """
        logging.info(f"Creating index {index_name} with the following schema: {json.dumps(mapping, indent=2)}")
        self.es_client.indices.create(index=index_name, ignore=400, body=mapping)

    def populate_index(self, path: str, index_name: str) -> None:
        """
        Populate an index from a CSV file.
        :param path: The path to the CSV file.
        :param index_name: Name of the index to which documents should be written.
        """
        # df = pd.read_csv(path, sep='delimiter', header=None).replace({np.nan: None})
        # logging.info(f"Writing {len(df.index)} documents to ES index {index_name}")
        # for doc in df.apply(lambda x: x.to_dict(), axis=1):
        #     self.es_client.index(index=index_name, id=1, body=json.dumps(doc))
        lines = []
        with open(path, mode='r') as file:
            csvFile = csv.DictReader(file, delimiter="\t")
            for line in csvFile:
                lines.append(line)
        bulk_data = []
        for i, row in enumerate(lines):
            bulk_data.append(
                {
                    "_index": index_name,
                    "_id": i,
                    "_source": {
                        "image_index": row["index"],
                        "bedrooms": float(row["bedrooms"]),
                        "bathrooms": float(row["bathrooms"]),
                        "longitude": float(row["longitude"]),
                        "latitude": float(row["latitude"]),
                        "house_age": int(row["house_age"]),
                        "sea_proximity": row["sea_proximity"],
                        "schools_rating": int(row["schools_rating"]),
                        "house_flooring": row["house_flooring"],
                        "area": int(row["area"]),
                        "house_public_transport": row["house_public_transport"],
                        "neighborhood_features": row["neighborhood_features"],
                        "price": int(row["price"]),

                    }
                }
            )
        bulk(self.es_client, bulk_data)
