# Property-Recommendation-System
This repo contains code for a LLM prompting and ElasticSearch based recommendation system for house properties.

# Workflow
<p align="center">
  <img width="569" alt="property-recommendation-system-workflow" src="https://github.com/iwinterknight/Property-Recommendation-System/assets/37212007/e0917af4-af62-41c9-8ff4-5ae0ab5fd790">
</p>
The figure above illustrates the synchronous workflow of the various components of the recommendation system.

The front end serves the user with a list of questions in a dialogue setting, to identify the user's requirements when prospecting houses. These questions are diverse in nature and capture basic details like `number of bedrooms`, `square footage of carpet area` etc., and more nuanced preferences such as `proximity to mode of transport`, `east facing` etc.

House details are stored in the form of ElasticSearch index hosted in a standalone container. The Natural Language Understanding(NLU) pipeline is responsible for joint intent detection and slot tagging on the user's responses. This is achieved through fine-tuned models hosted with the system and via prompting open sourced LLM APIs. 

The captured information(slots + intents) is used to form an ElasticSearch query to retrieve candidate listings. The client backend orchestrates the functions of the different components. It communicates with the different components via REST API calls. 

# Dataset and Models
# Dataset
# SoCal
Socal is a house price prediction dataset comprising of house attributes and images.

| image_id | street                                 | citi                       | n_citi | bed | bath | sqft  | price   |
| -------- | -------------------------------------- | -------------------------- | ------ | --- | ---- | ----- | ------- |
| 0        | 1317 Van Buren Avenue                  | Salton City, CA            | 317    | 3   | 2    | 1560  | 201900  |
| 1        | 124 C Street W                         | Brawley, CA                | 48     | 3   | 2    | 713   | 228500  |
| 2        | 2304 Clark Road                        | Imperial, CA               | 152    | 3   | 1    | 800   | 273950  |
| 3        | 755 Brawley Avenue                     | Brawley, CA                | 48     | 3   | 1    | 1082  | 350000  |
| 4        | 2207 R Carrillo Court                  | Calexico, CA               | 55     | 4   | 3    | 2547  | 385100  |
| 5        | 755 Brawley Avenue                     | Brawley, CA                | 48     | 3   | 1    | 1082  | 350000  |
| 6        | 1100 CAMILIA Street                    | Calexico, CA               | 55     | 4   | 3    | 2769  | 415000  |
| 7        | 803 Chaparral Court                    | Brawley, CA                | 48     | 5   | 2.1  | 2600  | 545000  |
| 8        | 803 Chaparral Court                    | Brawley, CA                | 48     | 5   | 2.1  | 2600  | 545000  |
| 9        | 2306 Lark Court                        | Salton City, CA            | 317    | 4   | 5.1  | 3932  | 690000  |
| 10       | 38833 Gorman Post Road                 | Gorman, CA                 | 129    | 3   | 2.1  | 4044  | 1350000 |
Sample rows from the SoCal dataset (https://www.kaggle.com/datasets/camnugent/california-housing-prices)
