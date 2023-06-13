housing_features_mapping = {
    "mappings": {
        "properties": {
            # "index": {"type": "integer"},
            "bedrooms": {"type": "integer"},
            "bathrooms": {"type": "float"},
            "longitude": {"type": "float"},
            "latitude": {"type": "float"},
            "house_age": {"type": "integer"},
            "sea_proximity": {"type": "text"},
            "schools_rating": {"type": "integer"},
            "house_flooring": {"type": "text"},
            "area": {"type": "integer"},
            "house_public_transport": {"type": "text"},
            "neighborhood_features": {"type": "text"},
            "price": {"type": "integer"}
        }
    }
}

netflix_mapping = {
    "mappings": {
        "properties": {
            "show_id": {"type": "text"},
            "type": {"type": "text"},
            "title": {"type": "text"},
            "director": {"type": "text"},
            "cast": {"type": "text"},
            "country": {"type": "text"},
            "date_added": {"type": "text"},
            "release_year": {"type": "integer"},
            "rating": {"type": "text"},
            "duration": {"type": "text"},
            "listed_in": {"type": "text"},
            "description": {"type": "text"},
        }
    }
}
