# -*- coding: utf-8 -*-
"""
Created on Tue Jan 12 15:10:19 2021

@author: Mark He

Process patent text
"""

## the function to keep the unique full names in a list
import re
import spacy
nlp = spacy.load("en")
import glob
import math
import pandas as pd
import uuid as uuid_gen

import collections
import pickle

import mysql.connector
from absl import app
from absl import flags
from absl import logging

from pv.disambiguation.core import AssigneeMention, AssigneeNameMention


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

FLAGS = flags.FLAGS
flags.DEFINE_string('feature_out', 'exp_out/', '')
flags.DEFINE_string('path', 'C:/Users/Liulihua/Dropbox/PatentAssigneeMatching/patents_data_eb/text/', '')
flags.DEFINE_string('project', 'C:/Users/Liulihua/Dropbox/PatentAssigneeMatching/', '')


def build_assignee():
    path = FLAGS.path
    feature_out = FLAGS.feature_out
    
    # read the list of texts
    
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
        
    result = {'assign':assign,'assign_content':assign_content,'add':add,'patentid':patentid,'uuid':uuid}
    result_dt = pd.DataFrame(result)
    result_dt.to_excel(feature_out + 'assign_rev_v4.xlsx')
    
    # | assignee | add | patentid | uuid |
    feature_map = collections.defaultdict(list)
    idx = 0
    while(idx <= len(result_dt)-1):
        rec = {'uuid':result_dt['uuid'][idx], 'patent_id':result_dt['patentid'][idx], 'organization':result_dt['assign'][idx]}
        am = AssigneeMention.from_doc(rec)
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
        anm = AssigneeNameMention.from_assignee_mentions(nm, feats[0][nm])
        for c in anm.canopies:
            canopies[c].add(anm.uuid)
        records[anm.uuid] = anm

    with open(FLAGS.feature_out + 'assignee_mentions.%s.pkl' % 'records', 'wb') as fout:
        pickle.dump(records, fout)
    with open(FLAGS.feature_out + 'assignee_mentions.%s.pkl' % 'canopies', 'wb') as fout:
        pickle.dump(canopies, fout)


if __name__ == "__main__":
    app.run(main)


    
    
    
    