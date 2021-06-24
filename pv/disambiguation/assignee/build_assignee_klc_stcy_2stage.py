# -*- coding: utf-8 -*-
"""
Created on Tue Jan 12 15:10:19 2021

@author: Mark He

Process patent text
"""

## the function to keep the unique full names in a list
import re
import glob
import math
import pandas as pd
import uuid as uuid_gen
import nltk
nltk.download('punkt')
import collections
from collections import Counter
import pickle

import mysql.connector
from absl import app
from absl import flags
from absl import logging

from pv.disambiguation.core import AssigneeMention_2stage, AssigneeNameMention_2stage


def symbol_corr(text):
    text = re.sub(r'(?<= [A-Z]), ','. ',text)
    return text

def revise_short(text,text_copy):
    if ' ' in text and len(text)>=7:
        return text
    else:
        text = (',').join(text_copy.split(',')[0:2])
        return text

def revise_assignor(text,text_copy):
    if len(re.compile('[Aa][Ss][Ss][Ii][Gg][Nn][Oo][A-Za-z]').findall(text))>0:
        text_copy = re.sub(r', [Bb][Yy] .*?,','',text_copy)
        text_copy = re.sub(r'.*?(?<![A-Za-z])[Tt][Oo](?![A-Za-z])','|||',text_copy)
        text_copy = re.sub(r'\|\|\|.','',text_copy)
        text = (',').join(text_copy.split(',')[0:1])
        text = re.sub(r'[Aa][Ss][Ss][Ii][Gg][Nn][Oo][Rr]','',text)
        return text
    else:
        return text

def foo(x): 
    m = pd.Series.mode(x); 
    return m.values[0] if not m.empty else ''
    
'''
def create_vote_name(sample):
    unique_entity = sample.copy()
    unique_entity = unique_entity['entity_id']
    unique_entity = unique_entity.drop_duplicates()
    unique_entity = unique_entity.reset_index(drop = True)

    vote_name_output = collections.defaultdict(list)
    idx = 0
    while(idx <= len(unique_entity)-1):
        name_sample = sample[sample['entity_id']==unique_entity[idx]]
        vote_name_temp = Counter(name_sample['assignee_name']).most_common(1)[0][0]
        vote_name_output[unique_entity[idx]].append(vote_name_temp)
        if idx%10000==0:
            print("finished {0}/{1}th".format(idx+1,len(unique_entity)))
        idx += 1
    return vote_name_output
'''
FLAGS = flags.FLAGS
flags.DEFINE_string('feature_out', '/kellogg/data/patents/output/', '')
flags.DEFINE_string('path', '/kellogg/data/patents/patent_text/', '')


def build_assignee():
    path = FLAGS.path
    feature_out = FLAGS.feature_out
    
    # read the list of texts
    '''
    file_list = glob.glob(path+"abbyy/US100/*.txt")
    assign = []
    add = []
    patentid = []
    uuid = []
    assign_content = []
    i = 0
    
    while(i <= len(file_list)-1):
        file = file_list[i]
        temp_text = open(file,encoding='utf-8').read() 
        temp_patentid = re.sub(path,'',file)
        temp_patentid = re.sub(r'abbyy/US100\\','',temp_patentid)
        temp_patentid = re.sub(r'.txt','',temp_patentid)
        # capture the sentence begins w/ Assign...
        assign_cap = re.compile('[Aa][Ss][Ss][Ii][Gg][Nn].*\n.*\n').findall(temp_text)
        assign_cap = assign_cap + re.compile('[Bb]y .*[Aa][Ss][Ss][Ii][Gg][Nn][Ee][Ee]').findall(temp_text)
        # split the sentence if the patent is assigned to multiple agents
        assign_cap_split = []
        for sent in assign_cap:
            sent = re.sub(r'ONE-.*? TO ','|| TO ',sent)
            if '||' in sent:
                assign_cap_split = assign_cap_split + sent.split('||')[1:]
            else:
                assign_cap_split = assign_cap_split + [sent]
                
        # revise the captured sentence
        assign_rev = []
        for sent in assign_cap_split:
            assign_content.append(sent)
            sent = re.sub(r'\n',' ',sent)
            # delete the part before the TO
            sent = symbol_corr(sent)
            sent = re.sub(r'.*? TO ','',sent)
            sent_copy = sent+''
            sent = sent.split(',')[0]
            # revise the extraction if too short
            sent = revise_short(sent,sent_copy)
            # revise the extraction if “assignor” is in the string
            sent = revise_assignor(sent,sent_copy)
            # extract the entities
            assign_rev = assign_rev + [sent]
        
        k = 1
        temp_uuid = []
        while(k<=len(assign_rev)):
            temp_uuid.append(str(uuid_gen.uuid4()))
            k = k+1
        temp_patentid = [temp_patentid]*len(assign_rev)   
        temp_add = [file]*len(assign_rev)  
        
        uuid = uuid + temp_uuid
        patentid = patentid + temp_patentid
        assign = assign + assign_rev
        add = add + temp_add
        if math.floor((i-1)/1000) != math.floor(i/1000):
            print("finished {0}/{1}".format(i,len(file_list)))
        i = i+1
    '''
    extract_assignee = pd.read_csv(feature_out + 'disambiguation_output.csv')  
    extract_assignee['patnum'] = extract_assignee['patnum'].apply(str)
    extract_assignee['assignee_name'] = extract_assignee['assignee_name'].apply(str)
    extract_assignee['uuid'] = extract_assignee['uuid'].apply(str)
    # extract_assignee['mention_id'] = ['%s-%s' % (extract_assignee['patnum'][i], extract_assignee['uuid'][i]) for i in range(len(extract_assignee))]
    extract_assignee['entity_id'] = extract_assignee['entity_id'].apply(str)

    # create the dict of most frequent name with entity_id as the key
    print("start revise the assignee name")
    vote_name = extract_assignee.groupby(['entity_id'])['assignee_name'].agg(foo)
    rev_name = []
    for i in range(len(extract_assignee)):
        rev_name.append(vote_name[extract_assignee['entity_id'][i]])
        if i%10000==0:
            print("finished {0}/{1}th".format(i+1,len(extract_assignee)))
    extract_assignee['rev_name'] = rev_name

    print(len(extract_assignee))
    # 6750000
    with open(FLAGS.feature_out + 'disambiguation_output_2stage.pkl', 'wb') as fout:
        pickle.dump(extract_assignee, fout)    
    # check  
    with open(FLAGS.feature_out + 'disambiguation_output_2stage.pkl', 'rb') as fin:  
        check = pickle.load(fin)
    print(len(check))
    print("generated uuids for each patent and saved the output")

    
    # | assignee | patentid | uuid |
    feature_map = collections.defaultdict(list)
    idx = 0
    while(idx <= len(extract_assignee)-1):
        rec = {'uuid':extract_assignee['uuid'][idx], 'patent_id':extract_assignee['patnum'][idx], 'organization':extract_assignee['rev_name'][idx]}
        am = AssigneeMention_2stage.from_doc(rec)
        # the key is the organization which is the assignee
        # the name_features return the cleaned name string[0] and 
        # noStopwords[1]
        feature_map[am.name_features()[0]].append(am)
        idx += 1
        logging.log_every_n(logging.INFO, 'Processed %s granted records - %s features', 10000, idx, len(feature_map))
        # the feature_map has the cleaned no blankspace name string as the key
        # and in each element, there is the unique id for the patent;        
    return feature_map    
 

def run(source):
    if source == 'document':
        features = build_assignee()
    return features


def main(argv):
    logging.info('Building assignee mentions')
    feats = [n for n in map(run, ['document'])]
    logging.info('finished loading mentions %s', len(feats))
    name_mentions = set(feats[0].keys())
    logging.info('number of name mentions %s', len(name_mentions))
    from tqdm import tqdm
    records = dict()
    from collections import defaultdict
    canopies = defaultdict(set)
    for nm in tqdm(name_mentions, 'name_mentions'):
        anm = AssigneeNameMention_2stage.from_assignee_mentions(nm, feats[0][nm])
        for c in anm.canopies:
            canopies[c].add(anm.uuid)
        records[anm.uuid] = anm

    with open(FLAGS.feature_out + 'assignee_mentions_2stage.%s.pkl' % 'records', 'wb') as fout:
        pickle.dump(records, fout)
    with open(FLAGS.feature_out + 'assignee_mentions_2stage.%s.pkl' % 'canopies', 'wb') as fout:
        pickle.dump(canopies, fout)


if __name__ == "__main__":
    app.run(main)

    
    
    
    