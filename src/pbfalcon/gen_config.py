"""Generate FALCON cfg (.ini file).

We plan to generate cfg in a complicated way.
But for now, we just use a look-up table,
based on ranges of the length of a genome.
"""
from falcon_kit import run_support as support
from . import tusks
import ConfigParser as configparser
import logging
import os
import re
import StringIO


#logging.basicConfig()
log = logging.getLogger(__name__)
#log.setLevel(logging.DEBUG)
OPTION_GENOME_LENGTH = 'A0_GenomeLength_str'
OPTION_CORES_MAX = 'B0_CoresMax_str'
OPTION_CFG = 'F0_FalconAdvanced_str'

defaults_old = """\
falcon_sense_option = --output_multi --min_idt 0.70 --min_cov 1 --local_match_count_threshold 100 --max_n_read 20000 --n_core 6
length_cutoff = 1
length_cutoff_pr = 1
pa_DBsplit_option = -x5 -s50 -a
pa_HPCdaligner_option =  -v -k25 -h35 -w5 -H1000 -e.95 -l40 -s1000 -t27
pa_concurrent_jobs = 32
overlap_filtering_setting = --max_diff 10000 --max_cov 100000 --min_cov 0 --bestn 1000 --n_core 4
ovlp_HPCdaligner_option =  -v -k25 -h35 -w5 -H1000 -e.99 -l40 -s1000 -t27
ovlp_DBsplit_option = -x5 -s50 -a
ovlp_concurrent_jobs = 32
"""
defaults_lambda = """\
falcon_sense_option = --output_multi --min_idt 0.70 --min_cov 4 --local_match_count_threshold 2 --max_n_read 200 --n_core 6
length_cutoff = 12000
length_cutoff_pr = 12000
pa_DBsplit_option = -x500 -s50
pa_HPCdaligner_option = -v -dal4 -t16 -e.70 -l1000 -s1000
pa_concurrent_jobs = 32
overlap_filtering_setting = --max_diff 100 --max_cov 50 --min_cov 1 --bestn 10 --n_core 24
ovlp_HPCdaligner_option = -v -dal4 -t32 -h60 -e.96 -l500 -s1000
ovlp_DBsplit_option = -x500 -s50
ovlp_concurrent_jobs = 32
"""
# also see:
#   https://dazzlerblog.wordpress.com/command-guides/daligner-command-reference-guide/
#   https://dazzlerblog.wordpress.com/2014/06/01/the-dazzler-db/
#   https://github.com/PacificBiosciences/FALCON/wiki/Manual

defaults = list(sorted([
    (    0, defaults_old),
    (10000, defaults_lambda),
]))


def sorted_str(s):
    return '\n'.join(sorted(s.splitlines()))

def _populate_falcon_options(options):
    length = int(options[OPTION_GENOME_LENGTH]) # required!
    index = 0
    # We could binary-search, but we will just walk thru.
    while index < len(defaults) - 1:
        if defaults[index+1][0] <= length:
            index += 1
    fc = ini2dict(sorted_str(defaults[index][1]))

    # Also keep everything except a few which could be mal-formatted.
    excluded = [OPTION_CFG]
    for key in options:
        if key not in excluded:
            fc[key] = options[key]
    return fc
    
def _options_dict_with_base_keys(options_dict, prefix='falcon_ns.task_options.'):
    """Remove leading namespaces from key names,
    in a copy of options_dict.

    prefix: should include trailing dot
    """
    new_dict = dict()
    for key, val in options_dict.items():
        if key.startswith(prefix):
            tail = key[len(prefix):]
            if '.' in tail:
                log.warning('prefix {!r} found on option {!r}'.format(
                    prefix, key))
            new_dict[tail] = val
    return new_dict

def _gen_config(options_dict):
    """Generate ConfigParser object from dict.
    """
    cfg = support.parse_config('')
    sec = "General"
    cfg.add_section(sec)
    for key, val in options_dict.items():
        # Strip leading and trailing ws, b/c the pbsmrtpipe
        # misinterprets XML as a data-interchanges language.
        # (It is only mark-up, so ws is never meaningful.)
        # Also, we want only strings; hopefully, we can fix
        # the TC later to drop the type-info (e.g. integer).
        cfg.set(sec, key, str(val).strip())
    return cfg

def _write_config(config, config_fn):
    with open(config_fn, 'w') as ofh:
        config.write(ofh)

def ini2dict(ini_text):
    ifp = StringIO.StringIO('[General]\n' + ini_text)
    cp = configparser.ConfigParser()
    cp.readfp(ifp)
    return dict(cp.items('General'))

re_semicolon = re.compile(r'\s*;+\s*')

def option_text2ini(option_text):
    # Basically, just translate semicolons into linefeeds.
    return re_semicolon.sub('\n', option_text)

re_newline = re.compile(r'\s*\n\s*', re.MULTILINE)

def ini2option_text(ini):
    # Basically, just translate linefeeds into semicolons.
    return re_newline.sub(';', ini)

def get_falcon_overrides(cfg_content, OPTION_CFG=OPTION_CFG):
    """options keys are bare (no namespaces)
    """
    if '\n' in cfg_content:
        log.error('linefeed found in option "%s", which is ok here but should have been prevented earler' %(
            OPTION_CFG))
        cfg_content = ini2option_text(cfg_content)
    if cfg_content.strip().startswith('['):
        log.error('Option "%s" seems to have .ini-style [brackets], which is an error. It is not really a .ini file.' %(
            OPTION_CFG))
        # Try to strip the first line, and hope there are no others.
        cfg_content = cfg_content[cfg_content.index(']'):]
    ini = option_text2ini(cfg_content)
    log.info(ini)
    # Now, parse the overrides, but skip it on any error.
    try:
        overrides = ini2dict(ini)
    except Exception as exc:
        log.exception('For option "%s" (for overrides) we had a problem parsing its contents:\n%s' %(
            OPTION_CFG, cfg_content))
        overrides = dict()
    return overrides

def run_falcon_gen_config(input_files, output_files, options):
    """Generate a config-file from options.

    TODO(CD):
    Eventually, use GenomeSize and ParallelTasksMax too.
    Also, validate cfg, in case of missing options.
    """
    i_fofn_fn, = input_files
    o_cfg_fn, = output_files
    import pprint
    log.info('options to run_falcon_gen_config:\n{}'.format(pprint.pformat(options)))
    options = _options_dict_with_base_keys(options)
    falcon_options = _populate_falcon_options(options)
    if OPTION_CFG in options:
        overrides = get_falcon_overrides(options[OPTION_CFG], OPTION_CFG)
        falcon_options.update(overrides)
    else:
        raise Exception("Could not find %s" %OPTION_CFG)
    config = _gen_config(falcon_options)
    with tusks.cd(os.path.dirname(i_fofn_fn)):
        return _write_config(config, o_cfg_fn) # Write lower-case keys, which is fine.

