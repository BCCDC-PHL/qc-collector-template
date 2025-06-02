import collections
import csv
import glob
import json
import logging
import os
import re
import shutil

from pathlib import Path
from typing import Iterator, Optional

import qc_collector.parsers as parsers


def create_output_dirs(config: dict):
    """
    Create output directories if they don't exist.

    :param config: Application config.
    :type config: dict[str, object]
    :return: None
    :rtype: None
    """
    base_outdir = config['output_dir']
    output_dirs = [
        base_outdir,
        os.path.join(base_outdir, 'library-qc'),
        # Add any other output dirs as needed
        # os.path.join(base_outdir, 'another-output'),
    ]
    for output_dir in output_dirs:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    return None


def find_analysis_dirs(config: dict):
    """
    Find all analysis directories with completed analyses.

    :param config: Application config.
    :type config: dict[str, object]
    :return: List of analysis directories.
    :rtype: Iterator[dict]
    """
    miseq_run_id_regex = "\\d{6}_M\\d{5}_\\d+_\\d{9}-[A-Z0-9]{5}"
    nextseq_run_id_regex = "\\d{6}_VH\\d{5}_\\d+_[A-Z0-9]{9}"
    gridion_run_id_regex = "\\d{8}_\\d{4}_X\\d+_[A-Z0-9]{8}_[a-z0-9]{8}"

    analysis_by_run_dir = config['analysis_by_run_dir']
    subdirs = os.scandir(analysis_by_run_dir)

    for subdir in subdirs:
        run_id = subdir.name
        matches_miseq_regex = re.match(miseq_run_id_regex, run_id)
        matches_nextseq_regex = re.match(nextseq_run_id_regex, run_id)
        matches_gridion_regex = re.match(gridion_run_id_regex, run_id)
        sequencer_type = None
        if matches_miseq_regex:
            sequencer_type = 'miseq'
        elif matches_nextseq_regex:
            sequencer_type = 'nextseq'
        elif matches_gridion_regex:
            sequencer_type = 'gridion'
        not_excluded = run_id not in config['excluded_runs']
        ready_to_collect = False

        # Adjust this path as necessary to 
        analysis_complete_path = os.path.join(subdir, 'analysis_complete.json')
        analysis_complete = os.path.exists(analysis_complete_path)
        ready_to_collect = analysis_complete

        matches_recognized_run_id_format = (
            (matches_miseq_regex is not None) or
            (matches_nextseq_regex is not None) or
            (matches_gridion_regex is not None)
        )
        conditions_checked = {
            "is_directory": subdir.is_dir(),
            "matches_recognized_run_id_format": matches_recognized_run_id_format,
            "not_excluded": not_excluded,
            "ready_to_collect": ready_to_collect,
        }
        
        conditions_met = list(conditions_checked.values())

        analysis_directory_path = os.path.abspath(subdir.path)
        analysis_dir = {
            "path": analysis_directory_path,
            "sequencer_type": sequencer_type,
        }
        
        if all(conditions_met):
            logging.info(json.dumps({
                "event_type": "analysis_directory_found",
                "sequencing_run_id": run_id,
                "analysis_directory_path": analysis_directory_path
            }))

            yield analysis_dir
        else:
            logging.debug(json.dumps({
                "event_type": "directory_skipped",
                "analysis_directory_path": os.path.abspath(subdir.path),
                "conditions_checked": conditions_checked
            }))
            yield None


def find_runs(config):
    """
    Finda all runs that have routine sequence QC data.

    :param config: Application config.
    :type config: dict[str, object]
    :return: List of runs. Keys: ['run_id', 'sequencer_type']
    :rtype: list[dict[str, str]]
    """
    logging.info(json.dumps({"event_type": "find_runs_start"}))
    runs = []
    all_analysis_dirs = sorted(list(os.listdir(config['analysis_by_run_dir'])))
    illumina_run_ids = filter(lambda x: re.match('\\d{6}_[VM]', x) != None, all_analysis_dirs)
    nanopore_run_ids = filter(lambda x: re.match('\\d{8}_\\d{4}_', x) != None, all_analysis_dirs)
    all_run_ids = sorted(list(illumina_run_ids) + list(nanopore_run_ids))
    for run_id in all_run_ids:
        if run_id in config['excluded_runs']:
            continue

        sequencer_type = None
        if re.match('\\d{6}_M\\d{5}_', run_id):
            sequencer_type = 'miseq'
        elif re.match('\\d{6}_VH\\d{5}_', run_id):
            sequencer_type = 'nextseq'
        elif re.match('\\d{8}_\\d{4}_', run_id):
            sequencer_type = 'nanopore'

        analysis_dir = os.path.join(config['analysis_by_run_dir'], run_id)

        run = {
            'run_id': run_id,
            'sequencer_type': sequencer_type,
        }
        runs.append(run)

    logging.info(json.dumps({
        "event_type": "find_runs_complete"
    }))

    return runs


def scan(config: dict[str, object]) -> Iterator[Optional[dict[str, str]]]:
    """
    Scanning involves looking for all existing runs and...

    :param config: Application config.
    :type config: dict[str, object]
    :return: A run directory to analyze, or None
    :rtype: Iterator[Optional[dict[str, object]]]
    """
    logging.info(json.dumps({"event_type": "scan_start"}))
    for analysis_dir in find_analysis_dirs(config):    
        yield analysis_dir

    
    
def collect_outputs(config: dict[str, object], analysis_dir: Optional[dict[str, str]]):
    """
    Collect QC outputs for a specific analysis dir.

    :param config: Application config.
    :type config: dict[str, object]
    :param analysis_dir: Analysis dir. Keys: ['path', 'sequencer_type', 'analysis_type']
    :type analysis_dir: dict[str, str]
    :return: 
    :rtype: 
    """
    # Short-circuit if `analysis_dir` is None
    if not analysis_dir:
        logging.warning(json.dumps({
            "event_type": "collect_outputs_skipped",
            "analysis_dir": analysis_dir,
        }))
        return None
    
    run_id = os.path.basename(analysis_dir['path'])
    

    # library-qc
    library_qc_by_library_id = {}
    library_qc_dst_file = os.path.join(config['output_dir'], "library-qc", run_id + "_library_qc.json")
    # If the library QC for the run already exists, we don't re-generate.
    # Remove the existing library QC from the output dir to trigger re-generation.
    if not os.path.exists(library_qc_dst_file):
        # fastp is a raw sequence QC tool that we use in many pipelines.
        # You can remove this if you don't use fastp in your analysis.
        #
        # You may need to adjust this glob, or add additional logic to check
        # for specific output directories.
        fastp_output_glob = os.path.join(analysis_dir['path'], '*', '*_fastp.csv')
        fastp_paths = glob.glob(fastp_output_glob)
        for fastp_path in fastp_paths:
            if os.path.exists(fastp_path):
                fastp = parsers.parse_fastp(fastp_path)
                for fastp_record in fastp:
                    library_id = fastp_record['sample_id']
                    if library_id not in library_qc_by_library_id:
                        library_qc_by_library_id[library_id] = {
                            'library_id': library_id,
                        }
                    library_qc_by_library_id[library_id]['num_bases'] = fastp_record['total_bases_before_filtering']
                    # Add any other fastp metrics you want to collect

        
        # QUAST is an assembly QC tool that we use in many pipelines.
        # You can remove this if you don't use QUAST in your analysis
        quast_output_glob = os.path.join(analysis_dir['path'], '*', '*_quast.csv')
        quast_paths = glob.glob(quast_output_glob)
        for quast_path in quast_paths:
            if os.path.exists(quast_path):
                quast = parsers.parse_quast(quast_path)
                for quast_record in quast:
                    assembly_id_split = quast_record['assembly_id'].split('_')
                    if len(assembly_id_split) > 0:
                        library_id = assembly_id_split[0]
                        if library_id in library_qc_by_library_id:
                            library_qc_by_library_id[library_id]['assembly_length'] = quast_record['total_length']
                            library_qc_by_library_id[library_id]['assembly_num_contigs'] = quast_record['num_contigs']
                            library_qc_by_library_id[library_id]['assembly_N50'] = quast_record['assembly_N50']


        # Add any other QC metric collection you'd like
        
        
        with open(library_qc_dst_file, 'w') as f:
            json.dump(list(library_qc_by_library_id.values()), f, indent=2)
            f.write('\n')

        logging.info(json.dumps({
            "event_type": "write_library_qc_complete",
            "run_id": run_id,
            "dst_file": library_qc_dst_file
        }))

        

    logging.info(json.dumps({
        "event_type": "collect_outputs_complete",
        "sequencing_run_id": run_id,
        "analysis_dir_path": analysis_dir['path']
    }))
