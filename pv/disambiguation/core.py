import uuid as uuid_gen

import numpy as np
from absl import logging

import pv.disambiguation.inventor.names as names
from pv.disambiguation.assignee.names import assignee_name_features_and_canopies
from pv.disambiguation.assignee.names import normalize_name
from pv.disambiguation.location.reparser import LOCATIONS


def clean_name(name_str):
    return name_str.replace('\"', '')


class AssigneeMention(object):
    def __init__(self, uuid, patent_id, organization):
        self.uuid = uuid.replace('\"', '')
        self.patent_id = patent_id.replace('\"', '') if patent_id is not None else None
        self.organization = organization.replace('\"', '') if organization else ''
        self._name_features = None
        self._canopies = None
        self.mention_id = '%s-%s' % (self.patent_id, self.uuid)

    def canopies(self):
        if self._canopies is None:
            self._name_features, self._canopies = assignee_name_features_and_canopies(self.assignee_name())
        return self._canopies

    def name_features(self):
        if self._name_features is None:
            self._name_features, self._canopies = assignee_name_features_and_canopies(self.assignee_name())
        return self._name_features

    def assignee_name(self):
        return self.organization


    @staticmethod
    def from_doc(rec):
        uuid = rec['uuid']
        patent_id = rec['patent_id']
        organization = rec['organization']
        return AssigneeMention(uuid, patent_id, organization)

    @staticmethod
    def from_master(rec):
        uuid = rec['uuid']
        # patent_id = rec['patent_id']
        organization = rec['organization']
        return AssigneeMention(uuid, None, organization)


class AssigneeNameMention(object):

    def __init__(self, uuid, name_hash, canopies, name_features, 
                 unique_exact_strings,mention_ids):
        self.uuid = uuid
        self.name_hash = name_hash
        self.name_features = name_features
        self.canopies = canopies
        self.mention_ids = mention_ids
        self.unique_exact_strings = unique_exact_strings
        self.normalized_most_frequent = normalize_name(max(self.unique_exact_strings.items(), key=lambda x: x[1])[0])

    @staticmethod
    def from_assignee_mentions(name_hash, assignee_mentions):
        anm_id = str(uuid_gen.uuid4())
        name_features = set()
        canopies = set()
        unique_exact_strings = dict()
        mention_ids = set()
        for m in assignee_mentions:
            name_features.update(m.name_features())
            canopies.update(m.canopies())
            mention_ids.add(m.mention_id)
            if m.assignee_name() not in unique_exact_strings:
                unique_exact_strings[m.assignee_name()] = 0
            unique_exact_strings[m.assignee_name()] += 1
        return AssigneeNameMention(anm_id, name_hash, canopies, name_features, unique_exact_strings,mention_ids)


def load_assignee_mentions(filename, st=0, N=np.Inf, skip_first_line=True):
    logging.info('Loading assignee mentions from %s', filename)
    with open(filename, 'r') as fin:
        for idx, line in enumerate(fin):
            if idx == 0 and skip_first_line:
                continue
            logging.log_every_n(logging.INFO, 'Loaded %s lines of %s', 1000, idx, filename)
            if idx > N:
                logging.info('Loaded %s lines of %s', idx, filename)
                return
            elif idx >= st:
                yield AssigneeMention.from_line(line)


class LawyerMention(object):
    def __init__(self, uuid, patent_id, raw_first, raw_last, organization, country, sequence):
        self.uuid = uuid.replace('\"', '')
        self.patent_id = patent_id.replace('\"', '')
        self.country = country.replace('\"', '')
        self.raw_first = raw_first.replace('\"', '')
        self.raw_last = raw_last.replace('\"', '')
        self.organization = organization.replace('\"', '')
        self.sequence = sequence.replace('\"', '')
        self.is_organization = len(organization) > 0

    def lawyer_name(self):
        if self.is_organization:
            return self.organization
        else:
            fn = self.first_name()
            ln = self.last_name()
            return 'fn:%s_ln:%s' % (fn[0] if fn else self.uuid, ln[0] if ln else self.uuid)

    def first_name(self):
        if self._first_name is None:
            self.compute_name_features()
        return self._first_name

    def first_initial(self):
        if self._first_initial is None:
            self.compute_name_features()
        return self._first_initial

    def middle_initial(self):
        if self._middle_initial is None:
            self.compute_name_features()
        return self._middle_initial

    def middle_name(self):
        if self._middle_name is None:
            self.compute_name_features()
        return self._middle_name

    def last_name(self):
        if self._last_name is None:
            self.compute_name_features()
        return self._last_name

    def suffixes(self):
        if self._suffixes is None:
            self.compute_name_features()
        return self._suffixes

    def compute_name_features(self):
        self._first_name = names.first_name(self.raw_first)
        self._first_initial = names.first_initial(self.raw_first)
        self._middle_name = names.middle_name(self.raw_first)
        self._middle_initial = names.middle_initial(self.raw_first)
        self._suffixes = names.suffixes(self.raw_last)
        self._last_name = names.last_name(self.raw_last)

    @staticmethod
    def from_line(line):
        "uuid"  "lawyer_id"     "patent_id"     "name_first"    "name_last"     "organization"  "country"       "sequence"
        splt = line.strip().split("\t")
        if len(splt) != 8:
            logging.warning('Error processing line %s', line)
            return None
        else:
            return LawyerMention(splt[0], splt[1], splt[3], splt[4], splt[5], splt[6], splt[7])


def load_lawyer_mentions(filename, st=0, N=np.Inf, skip_first_line=True):
    logging.info('Loading lawyer mentions from %s', filename)
    with open(filename, 'r') as fin:
        for idx, line in enumerate(fin):
            if idx == 0 and skip_first_line:
                continue
            logging.log_every_n(logging.INFO, 'Loaded %s lines of %s', 1000, idx, filename)
            if idx > N:
                logging.info('Loaded %s lines of %s', idx, filename)
                return
            elif idx >= st:
                yield LawyerMention.from_line(line)


class LocationMention(object):
    def __init__(self, uuid, city, state, country, latlong):
        self.uuid = uuid.replace('\"', '')
        self.city = city.replace('\"', '')
        self.country = country.replace('\"', '')
        self.state = state.replace('\"', '')
        self.latlong = latlong.replace('\"', '')
        self._location_string = '%s|%s|%s' % (self.city, self.state, self.country)

        self._reparsed = LOCATIONS.reparse(self.location_string())

        self._canonical_city = self._reparsed[0]
        self._canonical_state = self._reparsed[1]
        self._canonical_country = self._reparsed[2]
        self._canonical_string = '%s|%s|%s' % (self._canonical_city, self._canonical_state, self._canonical_country)

    def location_string(self):
        return self._location_string

    def canonical_string(self):
        return self._canonical_string

    @staticmethod
    def from_line(line):
        # "id"    "location_id"   "city"  "state" "country"       "latlong"
        splt = line.strip().split("\t")
        if len(splt) != 6:
            logging.warning('Error processing line %s', line)
            return None
        else:
            return LocationMention(splt[0], splt[1], splt[3], splt[4], splt[5])

    @staticmethod
    def from_application_sql_record(rec):

        #  | id | city | state | country | lattitude | longitude | filename | created_date | updated_date |
        uuid = rec[0]
        city = rec[1] if rec[1] else ''
        state = rec[2] if rec[2] else ''
        country = rec[3] if rec[3] else ''
        lattitude = rec[4]
        longitude = rec[5]
        filename = rec[6]
        created_date = rec[7]
        updated_date = rec[8]
        return LocationMention(uuid, city, state, country, '')

    @staticmethod
    def from_granted_sql_record(rec):
        # | id  | location_id  | city   | state | country | country_transformed | location_id_transformed |
        uuid = rec[0]
        location_id = rec[1]
        city = rec[2] if rec[2] else ''
        state = rec[3] if rec[3] else ''
        country = rec[4] if rec[4] else ''
        country_transformed = rec[5]
        return LocationMention(uuid, city, state, country, '')


class LocationNameMention(object):
    def __init__(self, uuid, city, state, country, record_ids, mention_ids):
        self.uuid = uuid.replace('\"', '')
        self.city = city.replace('\"', '')
        self.country = country.replace('\"', '')
        self.state = state.replace('\"', '')
        self._location_string = '%s|%s|%s' % (self.city, self.state, self.country)

        self._in_database = None
        self.num_records = len(mention_ids)
        self.record_ids = record_ids
        self.mention_ids = mention_ids

        self._reparsed = LOCATIONS.reparse(self.location_string())

        self._canonical_city = self._reparsed[0]
        self._canonical_state = self._reparsed[1]
        self._canonical_country = self._reparsed[2]
        self._canonical_string = '%s|%s|%s' % (self._canonical_city, self._canonical_state, self._canonical_country)

    def canonical_city(self):
        return self._canonical_city

    def canonical_state(self):
        return self._canonical_state

    def canonical_country(self):
        return self._canonical_country

    def canonical_string(self):
        return self._canonical_string

    def location_string(self):
        return self._location_string

    @staticmethod
    def from_mentions(locationMentions):
        record_ids = set()
        mention_ids = set()
        for m in locationMentions:
            mention_ids.add(m.uuid)
        return LocationNameMention(str(uuid_gen.uuid4()), locationMentions[0]._canonical_city,
                                   locationMentions[0]._canonical_state,
                                   locationMentions[0]._canonical_country, record_ids, mention_ids)


def load_location_mentions(filename, st=0, N=np.Inf, skip_first_line=True):
    logging.info('Loading location mentions from %s', filename)
    with open(filename, 'r') as fin:
        for idx, line in enumerate(fin):
            if idx == 0 and skip_first_line:
                continue
            logging.log_every_n(logging.INFO, 'Loaded %s lines of %s', 1000, idx, filename)
            if idx > N:
                logging.info('Loaded %s lines of %s', idx, filename)
                return
            elif idx >= st:
                yield LocationMention.from_line(line)
