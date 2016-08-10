###################
# FALCON TASKS
from .. import tusks as pbfalcon
from pbcommand.cli import registry_builder, registry_runner
from pbcommand.models import (FileTypes, OutputFileType)
import logging
import os
import StringIO
import sys
cd = pbfalcon.cd

log = logging.getLogger(__name__)

TOOL_NAMESPACE = 'falcon_ns'
DRIVER_BASE = "python -m pbfalcon.tasks.basic "

#from . import pbcommand_quick as pbquick
#registry = pbquick.registry_builder(TOOL_NAMESPACE, DRIVER_BASE)
registry = registry_builder(TOOL_NAMESPACE, DRIVER_BASE)

# FT_FOFN = FileType(to_file_ns("generic_fofn"), "generic", "fofn", 'text/plain')
FT_FOFN = FileTypes.FOFN
FT_JSON = FileTypes.JSON
FT_CFG = FileTypes.CFG
FT_BASH = FileTypes.TXT
FT_DUMMY = FileTypes.TXT
FT_SUBREADS = FileTypes.DS_SUBREADS
FT_CONTIGS = FileTypes.DS_CONTIG
FT_FASTA = FileTypes.FASTA
FT_REPORT = FileTypes.REPORT
FT_LOG = FileTypes.LOG

def FT(file_type, basename, title):
    # (file_type_id, label, display_name, description, default_name)
    return OutputFileType(file_type.file_type_id,
                          basename + '_id',
                          title,
                          "description for {f}".format(f=file_type),
                          basename)
FT_DB = FT(FT_DUMMY, 'dazzler.db', "DAZZ_DB (implies dot-files too)")
FT_JSON_OUT = OutputFileType(FileTypes.JSON.file_type_id,
                             "json_id",
                             "JSON",
                             "Generic JSON file",
                             "file")
FT_FASTA_OUT = OutputFileType(FileTypes.FASTA.file_type_id,
                              "fasta_id",
                              "FASTA",
                              "FASTA sequences",
                              "reads")
FT_CONTIGS_OUT = OutputFileType(FileTypes.DS_CONTIG.file_type_id,
                              "contig_id",
                              "contigset",
                              "Contigset of polished FASTA sequences",
                              "polished.contigset")


FT_FOFN_OUT = OutputFileType(FileTypes.FOFN.file_type_id,
                             "fofn_id",
                             "FOFN of daligner input (.fasta paths, possibly relative)",
                             "file of file names of fasta input",
                             "file")
@registry('task_falcon_config_get_fasta', '0.0.0', [FT_CFG], [FT_FOFN_OUT], is_distributed=False)
def run_rtc(rtc):
  with cd(os.path.dirname(rtc.task.output_files[0])):
    return pbfalcon.run_falcon_config_get_fasta(rtc.task.input_files, rtc.task.output_files)

@registry('task_falcon_config', '0.0.0', [FT_CFG, FT_FOFN], [FT_JSON_OUT], is_distributed=False)
def run_rtc(rtc):
  with cd(os.path.dirname(rtc.task.output_files[0])):
    return pbfalcon.run_falcon_config(rtc.task.input_files, rtc.task.output_files)

FT_FOFN_OUT = OutputFileType(FileTypes.FOFN.file_type_id,
                             "fofn_id",
                             "FOFN of daligner input (absolute .fasta paths)",
                             "file of file names of fasta input",
                             "file")
@registry('task_falcon_make_fofn_abs', '0.0.0', [FT_FOFN], [FT_FOFN_OUT], is_distributed=False)
def run_rtc(rtc):
  with cd(os.path.dirname(rtc.task.output_files[0])):
    return pbfalcon.run_falcon_make_fofn_abs(rtc.task.input_files, rtc.task.output_files)

RDJ0_OUT = OutputFileType(FileTypes.TXT.file_type_id,
                             "run_daligner_jobs0_id",
                             "bash file from HPC.daligner, stage-0",
                             "bash script",
                             "run_daligner_jobs0.sh")
@registry('task_falcon0_build_rdb', '0.0.0', [FT_JSON, FT_FOFN], [RDJ0_OUT, FT_DB, FT(FT_DUMMY, 'job.done', "Status file")], is_distributed=True)
def run_rtc(rtc):
  with cd(os.path.dirname(rtc.task.output_files[0])):
    return pbfalcon.run_falcon_build_rdb(rtc.task.input_files, rtc.task.output_files)

FT_FOFN_OUT = OutputFileType(FileTypes.FOFN.file_type_id,
                             "fofn_id",
                             "FOFN of daligner output (unmerged .las, stage-0)",
                             "file of file names of local-alignment output",
                             "file")
@registry('task_falcon0_run_daligner_jobs', '0.0.0', [FT_JSON, RDJ0_OUT], [FT_FOFN_OUT], is_distributed=True, nproc=4)
def run_rtc(rtc):
  with cd(os.path.dirname(rtc.task.output_files[0])):
    return pbfalcon.run_daligner_jobs(rtc.task.input_files, rtc.task.output_files, db_prefix='raw_reads')

# Typically, 6 procs for falcon_sense, but really that is set in cfg.
# We run each block on a single machine because we currently use python 'multiproc'.
# We run one 6-proc job for each block, serially.
# Too many could swamp NFS, so serial on one machine is fine, for now, until we measure.
# We pipe the result of LA4Falcon to the main process, which means that each fork consumes that much memory;
# that is the main impact on other processes on the same machine, typically 6GB altogether.
# Because this is I/O bound, we do not really harm the machine we are on,
# but we need to reserve some memory. nproc=6 is more than enough.
# TODO: Move into /tmp, to reduce the burden on NFS. Then we might chunk.
FT_FOFN_OUT = OutputFileType(FileTypes.FOFN.file_type_id,
                             "fofn_id",
                             "FOFN of daligner output (merged .las, stage-0)",
                             "file of file names of local-alignment output",
                             "file")
@registry('task_falcon0_run_merge_consensus_jobs', '0.0.0', [FT_JSON, RDJ0_OUT, FT_FOFN], [FT_FOFN_OUT], is_distributed=True, nproc=6)
def run_rtc(rtc):
  with cd(os.path.dirname(rtc.task.output_files[0])):
    return pbfalcon.run_merge_consensus_jobs(rtc.task.input_files, rtc.task.output_files, db_prefix='raw_reads')

# Run similar steps for preads.
RDJ1_OUT = OutputFileType(FileTypes.TXT.file_type_id,
                             "run_daligner_jobs1_id",
                             "bash file from HPC.daligner, stage-1",
                             "bash script",
                             "run_daligner_jobs1.sh")
@registry('task_falcon1_build_pdb', '0.0.0', [FT_JSON, FT_FOFN], [RDJ1_OUT], is_distributed=False)
def run_rtc(rtc):
  with cd(os.path.dirname(rtc.task.output_files[0])):
    return pbfalcon.run_falcon_build_pdb(rtc.task.input_files, rtc.task.output_files)

FT_FOFN_OUT = OutputFileType(FileTypes.FOFN.file_type_id,
                             "fofn_id",
                             "FOFN of daligner output (unmerged .las, stage-1)",
                             "file of file names of local-alignment output",
                             "file")
@registry('task_falcon1_run_daligner_jobs', '0.0.0', [FT_JSON, RDJ1_OUT], [FT_FOFN_OUT], is_distributed=True, nproc=4)
def run_rtc(rtc):
  with cd(os.path.dirname(rtc.task.output_files[0])):
    return pbfalcon.run_daligner_jobs(rtc.task.input_files, rtc.task.output_files, db_prefix='preads')

# Actually, this skips consensus, unlike falcon0_run_merge
FT_FOFN_OUT = OutputFileType(FileTypes.FOFN.file_type_id,
                             "fofn_id",
                             "FOFN of daligner output (merged .las, stage-1)",
                             "file of file names of local-alignment output",
                             "file")
@registry('task_falcon1_run_merge_consensus_jobs', '0.0.0', [FT_JSON, RDJ1_OUT, FT_FOFN], [FT_FOFN_OUT], is_distributed=True, nproc=1)
def run_rtc(rtc):
  with cd(os.path.dirname(rtc.task.output_files[0])):
    return pbfalcon.run_merge_consensus_jobs(rtc.task.input_files, rtc.task.output_files, db_prefix='preads')

@registry('task_falcon2_run_asm', '0.0.0', [FT_JSON, FT_FOFN], [FT_FASTA_OUT], is_distributed=True)
def run_rtc(rtc):
  with cd(os.path.dirname(rtc.task.output_files[0])):
    return pbfalcon.run_falcon_asm(rtc.task.input_files, rtc.task.output_files)

@registry('task_hgap_run', '0.0.0',
        [FT_JSON, FT_JSON, FT_SUBREADS],
        [FT_CONTIGS_OUT,
         FT(FT_REPORT, 'preassembly_rpt', "Preassembly report"),
         FT(FT_REPORT, 'polished_assembly_rpt', "Polished assembly report"),
         FT(FT_LOG, 'out2', "Another log output, experimentally"),
        ],
        is_distributed=False)
def run_rtc(rtc):
  with cd(os.path.dirname(rtc.task.output_files[0])):
    return pbfalcon.run_hgap(rtc.task.input_files, rtc.task.output_files)

@registry('task_report_preassembly_yield', '0.0.0', [FT_JSON, FT_FOFN, FT_DB], [FT(FT_REPORT, 'preassembly_yield', "Preassembly report")], is_distributed=False)
def run_rtc(rtc):
  with cd(os.path.dirname(rtc.task.output_files[0])):
    return pbfalcon.run_report_preassembly_yield(rtc.task.input_files, rtc.task.output_files)

if __name__ == '__main__':
    from falcon_kit import run_support
    run_support.logger = logging.getLogger("fc_run")
    sys.exit(registry_runner(registry, sys.argv[1:]))
