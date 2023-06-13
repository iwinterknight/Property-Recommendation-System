import io
import json
import os
import shutil
import nltk
import en_core_web_sm
from collections import OrderedDict
from flask import Flask
from snips_nlu import SnipsNLUEngine
from snips_nlu.default_configs import CONFIG_EN
from spacy.lang.en import English
from spacy.training import offsets_to_biluo_tags
from nltk import word_tokenize, pos_tag, ne_chunk
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')

nlp = en_core_web_sm.load()

app = Flask(__name__)


model_dir_listing_lq = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trained_model_listing_lq")


sentences = ["This is an example sentence", "Each sentence is converted"]

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


def get_closest_sentence(reference, sentences):
    ref_embed =  model.encode(reference)
    sent_embeddings = model.encode(sentences)
    max_sim, max_sim_index = 0.0, None
    for i, sent_embed in enumerate(sent_embeddings):
        sim = cosine_similarity(ref_embed.reshape((1, ref_embed.shape[0])), sent_embed.reshape((1, sent_embed.shape[0])))[0][0]
        if sim > max_sim:
            max_sim = sim
            max_sim_index = i
    return sentences[max_sim_index]


def preprocess(text):
    if not text:
        return None

    # text = text.lower()
    text = text.strip()
    punct_lookup = {}
    punct = '!"\'()*+,/;<=>@[\\]^_`{|}~'

    for char in punct:
        if char == "~":
            punct_lookup[ord(char)] = " around "
        else:
            punct_lookup[ord(char)] = " "

    text = text.strip(".")
    text = text.strip("?")
    text = text.strip("!")

    return text.translate(punct_lookup)


def train_snips_nlu(model_dir):
    with io.open("data/dataset.json") as f:
        dataset = json.load(f)

    seed = 42
    engine = SnipsNLUEngine(config=CONFIG_EN, random_state=seed)
    engine.fit(dataset)

    engine.persist(model_dir)

    return engine


def semantic_abstraction(text):
    chunked = ne_chunk(pos_tag(word_tokenize(text)))
    nlp = en_core_web_sm.load()
    doc = nlp(text)

    return chunked, doc, [(X, X.ent_iob_, X.ent_type_) for X in doc]


def entity_filtering_rules(text, ent_name, ent_value, start_index, end_index, semantic_entities):
    snippet = text[start_index:end_index]
    for X in semantic_entities:
        if ent_name == "numBedrooms" or ent_name == "numBathrooms":
            if ent_value < 1 or ent_value > 6:
                return None

            if ent_name == "numBedrooms":
                mistag = True
                snippet_ = snippet.lower()
                for name in ["bed", "bedroom", "bedrooms", "bhk"]:
                    if snippet_.find(name) != -1:
                        mistag = False
                if mistag:
                    return None

            if ent_name == "numBathrooms":
                mistag = True
                snippet_ = snippet.lower()
                for name in ["bath", "bathrooms", "bathrooms", "bhk"]:
                    if snippet_.find(name) != -1:
                        mistag = False
                if mistag:
                    return None

        if X.ent_type_ == "MONEY":
            # print(snippet, X)
            if snippet.find(str(X)) != -1:
                return "apartmentPrice"
        if snippet.find("$") != -1:
            return "apartmentPrice"

    return ent_name


def output_entity_tagging(data, chunked, semantic_entities):
    nlp = English()

    for datum in data:
        intent = datum['intent']['intentName']
        text = datum['input']
        annots = datum['slots']

        all_entities = []
        filtered_entities = []
        for i, an in enumerate(annots):
            ent_name = an['slotName']
            ent_range_start = an['range']['start']
            ent_range_end = an['range']['end']

            if 'kind' in an['value']:
                if an['value']['kind'] == 'TimeInterval':
                    filtered_entities.append(("from-time", an['value']['from'], ent_range_start, ent_range_end))
                    filtered_entities.append(("to-time", an['value']['to'], ent_range_start, ent_range_end))
                else:
                    ent_value = an['value']['value']
                    revised_ent_name = entity_filtering_rules(text, ent_name, ent_value, ent_range_start, ent_range_end,
                                                              semantic_entities)
                    if revised_ent_name:
                        # print("REVISED ENTITY NAME : {}\tREVISED ENTITY NAME : {}".format(ent_name, revised_ent_name))
                        an['slotName'] = revised_ent_name
                        filtered_entities.append((ent_name, ent_value, ent_range_start, ent_range_end))

            all_entities.append((ent_range_start, ent_range_end, ent_name))

        listing_desc_entity = []
        for i, entity_span in enumerate(semantic_entities.doc.ents):
            if entity_span.label_ in ['ORG', 'PERSON', 'GPE', 'FAC']:
                if len(listing_desc_entity) > 0 and listing_desc_entity[i - 1][3] + 1 >= entity_span.start_char and \
                        listing_desc_entity[i - 1][0] in ['CARDINAL', 'ORDINAL']:
                    filtered_entities.append(("listingDesc", listing_desc_entity[i - 1][1],
                                              listing_desc_entity[i - 1][2], listing_desc_entity[i - 1][3]))
                filtered_entities.append(
                    ("listingDesc", entity_span.lemma_, entity_span.start_char, entity_span.end_char))
            listing_desc_entity.append(
                (entity_span.label_, entity_span.lemma_, entity_span.start_char, entity_span.end_char))

        for j, entity_span in enumerate(semantic_entities.doc.ents):
            if entity_span.label_ == 'DATE':
                filtered_entities.append(("date", entity_span.lemma_, entity_span.start_char, entity_span.end_char))
            elif entity_span.label_ == 'TIME':
                filtered_entities.append(("time", entity_span.lemma_, entity_span.start_char, entity_span.end_char))
            listing_desc_entity.append(
                (entity_span.label_, entity_span.lemma_, entity_span.start_char, entity_span.end_char))

        for i, chunk in enumerate(chunked):
            if type(chunk) == nltk.tree.Tree:
                for node in chunk:
                    if node[1] == "NNP":
                        filtered_entities.append(("listingDesc", node[0], 0, len(text)))
            elif chunk[1] == "NNP":
                filtered_entities.append(("listingDesc", chunk[0], 0, len(text)))

        doc = nlp(text)
        tags = offsets_to_biluo_tags(doc, all_entities)
        # print(tags, intent)
        # print("\n")

        trimmed_filtererd_entities = []
        desc_entities = []
        desc_start, desc_end = float('inf'), float('-inf')
        for ent in filtered_entities:
            if ent[0] == "listingDesc":
                if ent[1].strip() not in desc_entities:
                    desc_entities.append(ent[1].strip())
                    if ent[2] < desc_start:
                        desc_start = ent[2]
                    if ent[3] > desc_end:
                        desc_end = ent[3]
            else:
                trimmed_filtererd_entities.append(ent)
        listing_desc_string = " ".join(desc_entities)
        # listing_desc_string = re.sub(r"(.+?)\1+", r"\1", listing_desc_string)

        if len(desc_entities) == 0:
            desc_start = 0
            desc_end = 0
        trimmed_filtererd_entities.append(("listingDesc", listing_desc_string, desc_start, desc_end))

        return trimmed_filtererd_entities, intent


def extract_intents_slots(query, intent, train='False'):
    model_dir = None
    if intent == "lead_qualification":
        model_dir = model_dir_listing_lq

    if train == 'True':
        if os.path.exists(model_dir):
            shutil.rmtree(model_dir)
        engine = train_snips_nlu(model_dir)
    else:
        engine = SnipsNLUEngine.from_path(model_dir)

    query = preprocess(query)

    chunked, semantic_entities, extracted_entities = semantic_abstraction(query)
    parsing = engine.parse(query)

    # print(parsing)

    refined_entities, intent = output_entity_tagging([parsing], chunked, semantic_entities)

    output = {"intent": intent}
    for refined in refined_entities:
        tagged_slots = OrderedDict()
        slot_type = refined[0]
        slot_value = refined[1]
        start_index = refined[2]
        end_index = refined[3]
        output[slot_type] = slot_value


    # output = []
    # for refined in refined_entities:
    #     tagged_slots = OrderedDict()
    #     slot_type = refined[0]
    #     slot_value = refined[1]
    #     start_index = refined[2]
    #     end_index = refined[3]
    #
    #     tagged_slots['1_slot_type'] = slot_type
    #     tagged_slots['2_slot_value'] = slot_value
    #     tagged_slots['3_start_index'] = start_index
    #     tagged_slots['4_end_index'] = end_index
    #
    #     output.append(tagged_slots)
    # output.append({"intent": intent})

    return output
