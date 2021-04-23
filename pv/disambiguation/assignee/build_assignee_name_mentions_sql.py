import collections
import pickle

import mysql.connector
from absl import app
from absl import flags
from absl import logging
import pandas as pd
from pv.disambiguation.core_dup import AssigneeMention, AssigneeNameMention
import numpy as np

FLAGS = flags.FLAGS
flags.DEFINE_string('feature_out', 'exp_out/duplicate/assignee_mentions', '')

import os


def last_name(im):
    return im.last_name()[0] if len(im.last_name()) > 0 else im.uuid


def build_pregrants():
    # | id | document_number | sequence | name_first | name_last | organization | type | rawlocation_id | city | state | country | filename | created_date | updated_date |
    rawdata = pd.read_excel('C:/RA/textual_analysis_innovation/data/replication/rawassignee_sample.xlsx')
    feature_map = collections.defaultdict(list)
    idx = 0
    for idx in range(len(rawdata)):
        rec = [rawdata['uuid'][idx],
               rawdata['uuid'][idx],
               rawdata['uuid'][idx],
               rawdata['uuid'][idx],
               rawdata['uuid'][idx],
               rawdata['uuid'][idx],
               rawdata['uuid'][idx],
               rawdata['uuid'][idx],
        
        ]
        am = AssigneeMention.from_application_sql_record(rec)
        feature_map[am.name_features()[0]].append(am)
        logging.log_every_n(logging.INFO, 'Processed %s pregrant records - %s features', 10000, idx, len(feature_map))
    return feature_map


def build_granted():
    # | uuid | patent_id | assignee_id | rawlocation_id | type | name_first | name_last | organization | sequence |
    rawdata = pd.read_excel('resources/rawassignee_sample.xlsx')
    feature_map = collections.defaultdict(list)
    idx = 0
    for idx in range(len(rawdata)):
        temp_name_first = str(rawdata['name_first'][idx])
        if temp_name_first=='nan':
            temp_name_first = ''
        temp_name_last = str(rawdata['name_last'][idx])
        if temp_name_last=='nan':
            temp_name_last = ''
        rec = [rawdata['uuid'][idx],
               str(rawdata['patent_id'][idx]),
               str(rawdata['assignee_id'][idx]),
               str(rawdata['rawlocation_id'][idx]),
               str(rawdata['type'][idx]),
               temp_name_first,
               temp_name_last,
               str(rawdata['organization'][idx]),
               str(rawdata['sequence'][idx])]        
        am = AssigneeMention.from_granted_sql_record(rec)
        feature_map[am.name_features()[0]].append(am)
        idx += 1
        logging.log_every_n(logging.INFO, 'Processed %s granted records - %s features', 10000, idx, len(feature_map))
    return feature_map


def run(source):
    if source == 'pregranted':
        features = build_pregrants()
    elif source == 'granted':
        features = build_granted()
    return features


def main(argv):
    logging.info('Building assignee mentions')
    feats = [n for n in map(run, ['granted'])]
    # feats = [run('granted')]
    logging.info('finished loading mentions %s', len(feats))
    name_mentions = set(feats[0].keys())
    logging.info('number of name mentions %s', len(name_mentions))
    from tqdm import tqdm
    records = dict()
    from collections import defaultdict
    canopies = defaultdict(set)
    for nm in tqdm(name_mentions, 'name_mentions'):
        anm = AssigneeNameMention.from_assignee_mentions(nm, feats[0][nm])
        for c in anm.canopies:
            canopies[c].add(anm.uuid)
        records[anm.uuid] = anm

    with open(FLAGS.feature_out + '.%s.pkl' % 'records', 'wb') as fout:
        pickle.dump(records, fout)
    with open(FLAGS.feature_out + '.%s.pkl' % 'canopies', 'wb') as fout:
        pickle.dump(canopies, fout)


if __name__ == "__main__":
    app.run(main)
