#!/usr/bin/env python3
# Prove IPv4 and IPv6 default to different runtime state directories, so
# shorewall and shorewall6 do not overwrite each other's default.save. The
# generated script and the CLI must agree, or the wrapper and the script would
# look in different places for provider state.
import os
import re
import sys
import tempfile

REPO = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..")
sys.path.insert(0, os.path.join(REPO, "src"))
from shorewall_nft import cli  # noqa: E402
from shorewall_nft.compile import compile_config  # noqa: E402

fails = 0


def check(name, got, want):
    global fails
    if got == want:
        print("PASS", name)
    else:
        print("FAIL", name, repr(got), "!=", repr(want))
        fails += 1


os.environ.pop("SWNFT_STATE", None)
for family, conf, want in ((4, "0003-two-interfaces", "/var/run/shorewall-nft"),
                           (6, "0010-v6-two-interfaces", "/var/run/shorewall6-nft")):
    os.environ["SWNFT_FAMILY"] = str(family)
    check(f"cli default, family {family}", cli._state_dir(), want)
    with tempfile.TemporaryDirectory() as d:
        script = os.path.join(d, "fw")
        compile_config(os.path.join(REPO, "tests", "corpus", conf, "config"),
                       script + ".nft", family, script_path=script)
        m = re.search(r"^STATE=\$\{SWNFT_STATE:-([^}]*)\}", open(script).read(), re.M)
        check(f"script default, family {family}", m and m.group(1), want)

os.environ["SWNFT_STATE"] = "/x"
check("SWNFT_STATE still overrides", cli._state_dir(), "/x")
sys.exit(1 if fails else 0)
