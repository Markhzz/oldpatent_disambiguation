import os
import pickle

import numpy as np
import torch
import wandb
from absl import app
from absl import flags
from absl import logging
from grinch.agglom import Agglom

from pv.disambiguation.inventor.load_mysql import Loader
from pv.disambiguation.inventor.model import InventorModel

FLAGS = flags.FLAGS

flags.DEFINE_string('pregranted_canopies', 'data/inventor/canopies.pregranted.pkl', '')
flags.DEFINE_string('granted_canopies', 'data/inventor/canopies.granted.pkl', '')
# !!! missing input
flags.DEFINE_string('model', 'exp_out/disambiguation-inventor-patentsview/solo/1gylsq4m/model-1000.torch', '')

flags.DEFINE_string('patent_titles', 'data/inventor/title_features.both.pkl', '')
flags.DEFINE_string('coinventors', 'data/inventor/coinventor_features.both.pkl', '')
flags.DEFINE_string('assignees', 'data/inventor/assignee_features.both.pkl', '')
# !!! missing input
flags.DEFINE_string('title_model', 'exp_out/sent2vec/patents/2020-05-10-15-08-42/model.bin', '')

flags.DEFINE_string('rawinventor', '/iesl/data/patentsview/2020-06-10/rawinventor.tsv', 'data path')
flags.DEFINE_string('outprefix', 'exp_out', 'data path')
flags.DEFINE_string('run_id', 'run_3', 'data path')

flags.DEFINE_string('dataset_name', 'patentsview', '')
flags.DEFINE_string('exp_name', 'disambiguation-inventor', '')

flags.DEFINE_string('base_id_file', '', '')

flags.DEFINE_integer('chunk_size', 10000, '')
flags.DEFINE_integer('chunk_id', 1000, '')
flags.DEFINE_integer('min_batch_size', 900, '')

logging.set_verbosity(logging.INFO)


def handle_singletons(canopy2predictions, singleton_canopies, loader):
    for s in singleton_canopies:
        pgids, gids = loader.pregranted_canopies[s], loader.granted_canopies[s]
        assert len(pgids) == 1 or len(gids) == 1
        if gids:
            canopy2predictions[s] = [[gids[0]], [gids[0]]]
        else:
            canopy2predictions[s] = [[pgids[0]], [pgids[0]]]
    return canopy2predictions


def run_on_batch(all_pids, all_lbls, all_records, all_canopies, model, encoding_model, canopy2predictions):
    features = encoding_model.encode(all_records)
    # grinch = WeightedMultiFeatureGrinch(model, features, num_points=len(all_pids), max_nodes=3 * len(all_pids))
    grinch = Agglom(model, features, num_points=len(all_pids))
    grinch.build_dendrogram_hac()
    # grinch.get_score_batch(grinch.all_valid_internal_nodes())
    fc = grinch.flat_clustering(model.aux['threshold'])
    for i in range(len(all_pids)):
        if all_canopies[i] not in canopy2predictions:
            canopy2predictions[all_canopies[i]] = [[], []]
        canopy2predictions[all_canopies[i]][0].append(all_pids[i])
        canopy2predictions[all_canopies[i]][1].append('%s-%s' % (all_canopies[i], fc[i]))
    return canopy2predictions


def needs_predicting(canopy_list, results, loader):
    res = []
    for c in canopy_list:
        if c not in results or (c in canopy_list and len(results[c]) != loader.num_records(c)):
            res.append(c)
    return res


def form_canopy_groups(canopy_list, loader, min_batch_size=800):
    size_pairs = [(c, loader.num_records(c)) for c in canopy_list]
    batches = [[]]
    batch_sizes = [0]
    batch_id = 0
    for c, s in size_pairs:
        if batch_sizes[-1] < min_batch_size:
            batch_sizes[-1] += s
            batches[-1].append(c)
        else:
            batches.append([c])
            batch_sizes.append(s)
    return batches, batch_sizes, dict(size_pairs)


def batch(canopy_list, loader, min_batch_size=800):
    batches, batch_sizes, sizes = form_canopy_groups(canopy_list, loader, min_batch_size)
    for batch, batch_size in zip(batches, batch_sizes):
        if batch_size > 0:
            all_records = loader.load_canopies(batch)
            all_pids = [x.uuid for x in all_records]
            all_lbls = -1 * np.ones(len(all_records))
            all_canopies = []
            for c in batch:
                all_canopies.extend([c for _ in range(sizes[c])])
            yield all_pids, all_lbls, all_records, all_canopies


def run_batch(canopy_list, outdir, job_name='disambig', singletons=None):
    logging.info('need to run on %s canopies = %s ...', len(canopy_list), str(canopy_list[:5]))

    os.makedirs(outdir, exist_ok=True)
    results = dict()
    outfile = os.path.join(outdir, job_name) + '.pkl'
    num_mentions_processed = 0
    num_canopies_processed = 0
    if os.path.exists(outfile):
        with open(outfile, 'rb') as fin:
            results = pickle.load(fin)

    loader = Loader.from_flags(FLAGS)

    to_run_on = needs_predicting(canopy_list, results, loader)
    logging.info('had results for %s, running on %s', len(canopy_list) - len(to_run_on), len(to_run_on))

    if len(to_run_on) == 0:
        logging.info('already had all canopies completed! wrapping up here...')

    encoding_model = InventorModel.from_flags(FLAGS)
    weight_model = torch.load(FLAGS.model).eval()

    if to_run_on:
        for idx, (all_pids, all_lbls, all_records, all_canopies) in enumerate(
          batch(to_run_on, loader, FLAGS.min_batch_size)):
            logging.info('[%s] run_batch %s - %s of %s - processed %s mentions', job_name, idx, num_canopies_processed,
                         len(canopy_list),
                         num_mentions_processed)
            run_on_batch(all_pids, all_lbls, all_records, all_canopies, weight_model, encoding_model, results)
            num_mentions_processed += len(all_pids)
            num_canopies_processed += np.unique(all_canopies).shape[0]
            if idx % 10 == 0:
                wandb.log({'computed': idx + FLAGS.chunk_id * FLAGS.chunk_size, 'num_mentions': num_mentions_processed,
                           'num_canopies_processed': num_canopies_processed})
                logging.info('[%s] caching results for job', job_name)
                with open(outfile, 'wb') as fin:
                    pickle.dump(results, fin)

    with open(outfile, 'wb') as fin:
        pickle.dump(results, fin)


def run_singletons(canopy_list, outdir, job_name='disambig'):
    logging.info('need to run on %s canopies = %s ...', len(canopy_list), str(canopy_list[:5]))

    os.makedirs(outdir, exist_ok=True)
    results = dict()
    outfile = os.path.join(outdir, job_name) + '.pkl'
    num_mentions_processed = 0
    if os.path.exists(outfile):
        with open(outfile, 'rb') as fin:
            results = pickle.load(fin)

    loader = Loader.from_flags(FLAGS)

    to_run_on = needs_predicting(canopy_list, results, loader)
    logging.info('had results for %s, running on %s', len(canopy_list) - len(to_run_on), len(to_run_on))

    if len(to_run_on) == 0:
        logging.info('already had all canopies completed! wrapping up here...')

    if to_run_on:
        handle_singletons(results, to_run_on, loader)

    with open(outfile, 'wb') as fin:
        pickle.dump(results, fin)


def main(argv):
    logging.info('Running clustering - %s ', str(argv))
    wandb.init(project="%s-%s" % (FLAGS.exp_name, FLAGS.dataset_name))
    wandb.config.update(flags.FLAGS)

    loader = Loader.from_flags(FLAGS)
    all_canopies = set(loader.pregranted_canopies.keys()).union(set(loader.granted_canopies.keys()))
    singletons = set([x for x in all_canopies if loader.num_records(x) == 1])
    all_canopies_sorted = sorted(list(all_canopies.difference(singletons)), key=lambda x: (loader.num_records(x), x),
                                 reverse=True)
    logging.info('Number of canopies %s ', len(all_canopies_sorted))
    logging.info('Number of singletons %s ', len(singletons))
    logging.info('Largest canopies - ')
    for c in all_canopies_sorted[:10]:
        logging.info('%s - %s records', c, loader.num_records(c))
    outdir = os.path.join(FLAGS.outprefix, 'inventor', FLAGS.run_id)
    num_chunks = int(len(all_canopies_sorted) / FLAGS.chunk_size)
    logging.info('%s num_chunks', num_chunks)
    logging.info('%s chunk_size', FLAGS.chunk_size)
    logging.info('%s chunk_id', FLAGS.chunk_id)
    chunks = [[] for _ in range(num_chunks)]
    for idx, c in enumerate(all_canopies_sorted):
        chunks[idx % num_chunks].append(c)

    if FLAGS.chunk_id == 0:
        logging.info('Running singletons!!')
        run_singletons(list(singletons), outdir, job_name='job-singletons')

    run_batch(chunks[FLAGS.chunk_id], outdir, job_name='job-%s' % FLAGS.chunk_id)


if __name__ == "__main__":
    app.run(main)
