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

