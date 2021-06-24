import os
import pickle
import re
import numpy as np
from absl import logging
from grinch.features import EncodingModel
from grinch.features import FeatCalc, CentroidType
from grinch.features import HashingVectorizerFeatures, SKLearnVectorizerFeatures

from pv.disambiguation.assignee.names import normalize_name, clean, split, remove_stopwords


class EntityKBFeatures(object):
    def __init__(self, entity_info_file, name, get_field, norm=None):
        logging.info('building entity kb...')
        with open(entity_info_file, 'rb') as f:
            [self.entity_ids, self.entity_names] = pickle.load(f)
        self.emap = dict()
        self.missing_entities = ['army', 'navy']
        if not os.path.exists(entity_info_file + '.cache.pkl'):
            for idx in range(len(self.entity_ids)):
                logging.log_first_n(logging.INFO, 'entity kb: %s -> %s', 10, self.entity_names[idx], idx)
                logging.log_every_n_seconds(logging.INFO, 'entity kb: %s of %s', 10, idx, len(self.entity_ids))
                self.emap[self.entity_names[idx].lower()] = idx
                normalized = normalize_name(self.entity_names[idx])
                splt = split(normalized)
                cleaned = clean(splt)
                nostop = remove_stopwords(cleaned)
                if normalized not in self.emap:
                    self.emap[normalized] = idx
                if splt not in self.emap:
                    self.emap[splt] = idx
                if cleaned not in self.emap:
                    self.emap[cleaned] = idx
                if nostop not in self.emap:
                    self.emap[nostop] = idx
            for me in self.missing_entities:
                self.emap[me] = len(self.emap)
            with open(entity_info_file + '.cache.pkl', 'wb') as fout:
                pickle.dump(self.emap, fout)
        else:
            with open(entity_info_file + '.cache.pkl', 'rb') as fin:
                self.emap = pickle.load(fin)
        self.name = name
        self.get_field = get_field
        logging.info('building entity kb...done')

    def encode(self, things_to_encode):
        res = -1 * np.ones(len(things_to_encode), dtype=np.int32)
        for idx, x in enumerate(things_to_encode):
            if x.normalized_most_frequent in self.emap:
                logging.log_first_n(logging.INFO, 'in entity kb (normalized): %s %s', 10, x.normalized_most_frequent,
                                    self.emap[x.normalized_most_frequent])
                res[idx] = self.emap[x.normalized_most_frequent]
            else:
                splt_x = split(x.normalized_most_frequent)
                cleaned = clean(splt_x)
                # nostop = remove_stopwords(cleaned)
                if splt_x in self.emap:
                    logging.log_first_n(logging.INFO, 'in entity kb (split): %s %s', 10, splt_x, self.emap[splt_x])
                    res[idx] = self.emap[splt_x]
                elif cleaned in self.emap:
                    logging.log_first_n(logging.INFO, 'in entity kb (cleaned: %s %s', 10, cleaned, self.emap[cleaned])
                    res[idx] = self.emap[cleaned]
                # elif nostop in self.emap:
                #     logging.log_first_n(logging.INFO, 'in entity kb (nostop): %s %s', 10, nostop, self.emap[nostop])
                #     res[idx] = self.emap[nostop]
        return np.expand_dims(res, axis=-1)




class StateKBFeatures(object):
    def __init__(self, state_info_file, name, get_field, norm=None):
        logging.info('building state kb...')
        with open(state_info_file, 'rb') as f:
            state_interm = pickle.load(f)
        self.state_ids = [state_interm[i][1] for i in range(len(state_interm))]
        self.state_names = [state_interm[i][0] for i in range(len(state_interm))]
        self.emap = dict()
        for idx in range(len(self.state_ids)):
            logging.log_first_n(logging.INFO, 'state kb: %s -> %s', 10, self.state_names[idx], idx)
            logging.log_every_n_seconds(logging.INFO, 'state kb: %s of %s', 10, idx, len(self.state_ids))
            self.emap[self.state_names[idx].lower()] = self.state_ids[idx]
        self.name = name
        self.get_field = get_field
        logging.info('building state kb...done')

    def encode(self, things_to_encode):
        res = -1 * np.ones(len(things_to_encode), dtype=np.int32)
        for idx, x in enumerate(things_to_encode):
            if x.assignee_state in self.emap:
                logging.log_first_n(logging.INFO, 'in state kb (normalized): %s %s', 10, x.assignee_state,
                                    self.emap[x.assignee_state])
                res[idx] = self.emap[x.assignee_state]
            else:
                if x.assignee_state == x.assignee_state:
                    for state in list(self.emap.keys()):
                        rev_state = re.sub('.*\s(' + state + ')\s.*', r'\1', x.assignee_state).strip()   
                    if rev_state in self.emap:       
                        res[idx] = self.emap[rev_state]
                # nostop = remove_stopwords(cleaned)
        return np.expand_dims(res, axis=-1)


class CountryKBFeatures(object):
    def __init__(self, country_info_file, name, get_field, norm=None):
        logging.info('building country kb...')
        with open(country_info_file, 'rb') as f:
            country_interm = pickle.load(f)
        self.country_ids = [country_interm[i][1] for i in range(len(country_interm))]
        self.country_names = [country_interm[i][0] for i in range(len(country_interm))]
        self.emap = dict()
        for idx in range(len(self.country_ids)):
            logging.log_first_n(logging.INFO, 'country kb: %s -> %s', 10, self.country_names[idx], idx)
            logging.log_every_n_seconds(logging.INFO, 'country kb: %s of %s', 10, idx, len(self.country_ids))
            self.emap[self.country_names[idx].lower()] = self.country_ids[idx]
        self.name = name
        self.get_field = get_field
        logging.info('building country kb...done')

    def encode(self, things_to_encode):
        res = -1 * np.ones(len(things_to_encode), dtype=np.int32)
        for idx, x in enumerate(things_to_encode):
            if x.assignee_country in self.emap:
                logging.log_first_n(logging.INFO, 'in country kb (normalized): %s %s', 10, x.assignee_country,
                                    self.emap[x.assignee_country])
                res[idx] = self.emap[x.assignee_country]
        return np.expand_dims(res, axis=-1)


class EntityidKBFeatures(object):
    def __init__(self, entityid_info_file, name, get_field, norm=None):
        logging.info('building entityid kb...')
        with open(entityid_info_file, 'rb') as f:
            unique_entityid = pickle.load(f)
        unique_entityid = unique_entityid.reset_index(drop=True)
        self.unique_entityid = unique_entityid
        self.emap = dict()
        for idx in range(len(self.unique_entityid)):
            logging.log_first_n(logging.INFO, 'unique_entityid kb: %s -> %s', 10, self.unique_entityid[idx], idx)
            logging.log_every_n_seconds(logging.INFO, 'unique_entityid kb: %s of %s', 10, idx, len(self.unique_entityid))
            self.emap[self.unique_entityid[idx]] = idx + 1000
        self.name = name
        self.get_field = get_field
        logging.info('building entityid kb...done')

    def encode(self, things_to_encode):
        res = -1 * np.ones(len(things_to_encode), dtype=np.int32)
        for idx, x in enumerate(things_to_encode):
            logging.log_first_n(logging.INFO, 'in entityid kb (normalized): %s %s', 10, x.assignee_entityid,
                                self.emap[x.assignee_entityid])
            res[idx] = self.emap[x.assignee_entityid]
        return np.expand_dims(res, axis=-1)

class AssigneeModel(object):

    @staticmethod
    def from_flags(flgs):
        logging.info('Building Assignee Model...')

        # Features:
        name_features = HashingVectorizerFeatures('name_features', lambda x: x.name_features)
        locations = HashingVectorizerFeatures('locations', lambda x: x.location_strings)

        canopy_feat = HashingVectorizerFeatures('canopy', lambda x: x.canopies)
        entity_kb_feat = EntityKBFeatures('resources/permid_entity_info.pkl', 'entitykb', lambda x: x)
        state_kb_feat = StateKBFeatures('resources/assignee_state.pkl','statekb', lambda x: x)
        country_kb_feat = CountryKBFeatures('resources/assignee_country.pkl','countrykb', lambda x: x)
        # PatentID Features
        patent_id = HashingVectorizerFeatures('patentid', lambda x: x.record_id)
        # !!! place where the missing input was used
        name_tfidf = SKLearnVectorizerFeatures(flgs.assignee_name_model,
                                               'name_tfidf',
                                               lambda x: clean(split(x.normalized_most_frequent)))

        triples = [(state_kb_feat, FeatCalc.NO_MATCH, CentroidType.BINARY, False, True),
                   (country_kb_feat, FeatCalc.NO_MATCH, CentroidType.BINARY, False, True),
                   (entity_kb_feat, FeatCalc.NO_MATCH, CentroidType.BINARY, False, True),
                   (name_tfidf, FeatCalc.DOT, CentroidType.NORMED, False, False)]
        encoders = [t[0] for t in triples]
        feature_types = [t[1] for t in triples]
        centroid_types = [t[2] for t in triples]
        must_links = set([t[0].name for t in triples if t[3]])
        must_not_links = set([t[0].name for t in triples if t[4]])
        assert len(encoders) == len(feature_types)
        assert len(feature_types) == len(centroid_types)
        return EncodingModel(encoders,
                             'AssigneeModelWithApps',
                             {}, feature_types, centroid_types, must_links, must_not_links)


class AssigneeModel_2stage(object):

    @staticmethod
    def from_flags(flgs):
        logging.info('Building Assignee Model...')

        # Features:
        name_features = HashingVectorizerFeatures('name_features', lambda x: x.name_features)
        locations = HashingVectorizerFeatures('locations', lambda x: x.location_strings)

        canopy_feat = HashingVectorizerFeatures('canopy', lambda x: x.canopies)
        entity_kb_feat = EntityKBFeatures('resources/permid_entity_info.pkl', 'entitykb', lambda x: x)
        state_kb_feat = StateKBFeatures('resources/assignee_state.pkl','statekb', lambda x: x)
        country_kb_feat = CountryKBFeatures('resources/assignee_country.pkl','countrykb', lambda x: x)
        entityid_kb_feat = EntityidKBFeatures('/kellogg/data/patents/code/assignee_clustering_stcy/resources/uniqueentityid.pkl','entityidkb',lambda x: x)
        # PatentID Features
        patent_id = HashingVectorizerFeatures('patentid', lambda x: x.record_id)
        # !!! place where the missing input was used
        name_tfidf = SKLearnVectorizerFeatures(flgs.assignee_name_model,
                                               'name_tfidf',
                                               lambda x: clean(split(x.normalized_most_frequent)))

        triples = [(state_kb_feat, FeatCalc.NO_MATCH, CentroidType.BINARY, False, True),
                   (country_kb_feat, FeatCalc.NO_MATCH, CentroidType.BINARY, False, True),
                   (entityid_kb_feat, FeatCalc.NO_MATCH, CentroidType.BINARY, False, True),
                   (entity_kb_feat, FeatCalc.NO_MATCH, CentroidType.BINARY, False, True),
                   (name_tfidf, FeatCalc.DOT, CentroidType.NORMED, False, False)]
        encoders = [t[0] for t in triples]
        feature_types = [t[1] for t in triples]
        centroid_types = [t[2] for t in triples]
        must_links = set([t[0].name for t in triples if t[3]])
        must_not_links = set([t[0].name for t in triples if t[4]])
        assert len(encoders) == len(feature_types)
        assert len(feature_types) == len(centroid_types)
        return EncodingModel(encoders,
                             'AssigneeModelWithApps',
                             {}, feature_types, centroid_types, must_links, must_not_links)

class AssigneeModel_nolocation(object):

    @staticmethod
    def from_flags(flgs):
        logging.info('Building Assignee Model...')

        # Features:
        name_features = HashingVectorizerFeatures('name_features', lambda x: x.name_features)
        locations = HashingVectorizerFeatures('locations', lambda x: x.location_strings)

        canopy_feat = HashingVectorizerFeatures('canopy', lambda x: x.canopies)
        entity_kb_feat = EntityKBFeatures('resources/permid_entity_info.pkl', 'entitykb', lambda x: x)
        # PatentID Features
        patent_id = HashingVectorizerFeatures('patentid', lambda x: x.record_id)
        # !!! place where the missing input was used
        name_tfidf = SKLearnVectorizerFeatures(flgs.assignee_name_model,
                                               'name_tfidf',
                                               lambda x: clean(split(x.normalized_most_frequent)))

        triples = [(entity_kb_feat, FeatCalc.NO_MATCH, CentroidType.BINARY, False, True),
                   (name_tfidf, FeatCalc.DOT, CentroidType.NORMED, False, False)]
        encoders = [t[0] for t in triples]
        feature_types = [t[1] for t in triples]
        centroid_types = [t[2] for t in triples]
        must_links = set([t[0].name for t in triples if t[3]])
        must_not_links = set([t[0].name for t in triples if t[4]])
        assert len(encoders) == len(feature_types)
        assert len(feature_types) == len(centroid_types)
        return EncodingModel(encoders,
                             'AssigneeModelWithApps',
                             {}, feature_types, centroid_types, must_links, must_not_links)

class AssigneeModel_noconstraint(object):

    @staticmethod
    def from_flags(flgs):
        logging.info('Building Assignee Model...')

        # Features:
        name_features = HashingVectorizerFeatures('name_features', lambda x: x.name_features)
        locations = HashingVectorizerFeatures('locations', lambda x: x.location_strings)

        canopy_feat = HashingVectorizerFeatures('canopy', lambda x: x.canopies)
        entity_kb_feat = EntityKBFeatures('resources/permid_entity_info.pkl', 'entitykb', lambda x: x)
        # PatentID Features
        patent_id = HashingVectorizerFeatures('patentid', lambda x: x.record_id)
        # !!! place where the missing input was used
        name_tfidf = SKLearnVectorizerFeatures(flgs.assignee_name_model,
                                               'name_tfidf',
                                               lambda x: clean(split(x.normalized_most_frequent)))

        triples = [(name_tfidf, FeatCalc.DOT, CentroidType.NORMED, False, False)]
        encoders = [t[0] for t in triples]
        feature_types = [t[1] for t in triples]
        centroid_types = [t[2] for t in triples]
        must_links = set([t[0].name for t in triples if t[3]])
        must_not_links = set([t[0].name for t in triples if t[4]])
        assert len(encoders) == len(feature_types)
        assert len(feature_types) == len(centroid_types)
        return EncodingModel(encoders,
                             'AssigneeModelWithApps',
                             {}, feature_types, centroid_types, must_links, must_not_links)