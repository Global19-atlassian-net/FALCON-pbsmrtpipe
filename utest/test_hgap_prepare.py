from pbfalcon import hgap_prepare as mod
from nose.tools import assert_equal
from StringIO import StringIO

def test_learn_job_type_old():
    job_type, sge_option = mod.learn_job_type(StringIO(script_old))
    assert_equal(job_type, 'sge')
    assert_equal(sge_option, 'default')

def test_learn_jmsenv_ish_from_cluster_sh():
    jmsenv_ish = mod.learn_jmsenv_ish_from_cluster_sh(script_new)
    expected = "/pbi/dept/secondary/siv/smrtlink/smrtlink-bihourly/smrtsuite_183743/userdata/generated/config/jmsenv/jmsenv.ish"
    assert_equal(jmsenv_ish, expected)

def test_learn_job_type_from_jmsenv_ish():
    jmsenv_output = """\
JMS_TYPE=SGE
QUEUE=prod66
"""
    job_type, sge_option = mod.learn_job_type_from_jmsenv_ish(jmsenv_output)
    assert_equal(job_type, 'sge')
    assert_equal(sge_option, 'prod66')

def _learn_job_type_new():
    """We cannot run this because it makes a system call to an installed script,
    which will probably disappear soon.
    """
    job_type, sge_option = mod.learn_job_type(StringIO(script_new))
    assert_equal(job_type, 'sge')
    assert_equal(sge_option, 'prod66')

script_old = """\
#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset
qsub -S /bin/bash -sync y -V -q default -N job.7754426falcon_ns.tasks.task_hgap_prepare \
    -o "/home/UNIXHOME/cdunn/repo/pb/smrtanalysis-client/smrtanalysis/siv/testkit-jobs/sa3_pipelines/hgap5_fake/synth5k/job_output/tasks/falcon_ns.tasks.t
    -e "/home/UNIXHOME/cdunn/repo/pb/smrtanalysis-client/smrtanalysis/siv/testkit-jobs/sa3_pipelines/hgap5_fake/synth5k/job_output/tasks/falcon_ns.tasks.t
    -pe smp 16 \
    "/home/UNIXHOME/cdunn/repo/pb/smrtanalysis-client/smrtanalysis/siv/testkit-jobs/sa3_pipelines/hgap5_fake/synth5k/job_output/tasks/falcon_ns.tasks.task
exit $?
"""

script_new = """\
#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset
/pbi/dept/secondary/siv/smrtlink/smrtlink-bihourly/smrtsuite_183743/install/smrtlink-incremental_3.2.0.183743,183743-183743-183733-183698-183698/admin/bin/runjmscmd \
    --start \
    --jmsenv "/pbi/dept/secondary/siv/smrtlink/smrtlink-bihourly/smrtsuite_183743/userdata/generated/config/jmsenv/jmsenv.ish" \
    --jobname job.2355224falcon_ns.tasks.task_hgap_prepare \
    --stdoutfile "/pbi/dept/secondary/siv/smrtlink/smrtlink-bihourly/smrtsuite_183743/userdata/jobs_root/000/000189/tasks/falcon_ns.tasks.task_hgap_prepare-0/cluster.stdout" \
    --stderrfile "/pbi/dept/secondary/siv/smrtlink/smrtlink-bihourly/smrtsuite_183743/userdata/jobs_root/000/000189/tasks/falcon_ns.tasks.task_hgap_prepare-0/cluster.stderr" \
    --nproc "23" \
    --cmd "/pbi/dept/secondary/siv/smrtlink/smrtlink-bihourly/smrtsuite_183743/userdata/jobs_root/000/000189/tasks/falcon_ns.tasks.task_hgap_prepare-0/run.sh"
"""
