from pbfalcon import ini2xml as m
from nose.tools import assert_equal
from StringIO import StringIO

cfg = """\
[General]
overlap_filtering_setting = --max-diff 100 --max-cov 50 --min-cov 1 --bestn 10 --n-core 24
zother_setting = etc
"""

xml = """\
    <task-options>
        <option id="falcon_ns.task_options.overlap_filtering_setting">
            <value>
                --max-diff 100 --max-cov 50 --min-cov 1 --bestn 10 --n-core 24
            </value>
        </option>
        <option id="falcon_ns.task_options.zother_setting">
            <value>
                etc
            </value>
        </option>
    </task-options>
"""

def test_xml():
    ifp = StringIO(cfg)
    ofp = StringIO()
    m.convert(ifp, ofp)
    got = ofp.getvalue()
    assert_equal(xml.splitlines(), got.splitlines())
