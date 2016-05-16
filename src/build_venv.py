# -*- coding=utf-8 -*-

#   Copyright (c) 2010-2016, MIT Probabilistic Computing Project
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import os
import re
import shutil
import subprocess
import sys

from shell_utils import echo, run, outputof, venv_run, shellquote, check_python

BAYESDB_DISTRIBUTIONS=[
    # Keep HEAD at top so it is the lowest priority:
    {"bayesdb": "HEAD",
     "prereqs": [
         "numpy==1.11.0 --no-cache-dir",
         "matplotlib==1.4.3 --no-cache-dir",
         "pandas==0.18.1",
         ],
     "crosscat": "HEAD",
     "bayeslite": "HEAD",
     "bdbcontrib": "HEAD",
     "crosscat_tests": "./check.sh",
     "bayeslite_tests": "./check.sh tests shell/tests",
     "bdbcontrib_tests": "./check.sh tests examples/tests"},

    # In chronological order from here, so older versions have lower priority:
    {"bayesdb": "0.1.3",  # 2015 Nov 11
     "crosscat": "tags/v0.1.43",
     "bayeslite": "tags/v0.1.3",
     "bdbcontrib": "tags/v0.1.3",
     "crosscat_tests": "./check.sh",
     "bayeslite_tests": "./check.sh tests shell/tests",
     "bdbcontrib_tests": "./check.sh"},
    {"bayesdb": "0.1.4",  # 2016 Jan 06
     "prereqs": [ "flaky" ],
     "crosscat": "tags/v0.1.48",
     "bayeslite": "tags/v0.1.4",
     "bdbcontrib": "tags/v0.1.4",
     "crosscat_tests": "./check.sh",
     "bayeslite_tests": "./check.sh tests shell/tests",
     "bdbcontrib_tests": "./check.sh"},
    {"bayesdb": "0.1.5",  # 2016 Jan 14
     "prereqs": [ "flaky" ],
     "crosscat": "tags/v0.1.50",
     "bayeslite": "tags/v0.1.5",
     "bdbcontrib": "tags/v0.1.5",
     "crosscat_tests": "./check.sh",
     "bayeslite_tests": "./check.sh tests shell/tests",
     "bdbcontrib_tests": "./check.sh"},
    {"bayesdb": "0.1.6",  # 2016 Feb 12
     "prereqs": [ "flaky" ],
     "crosscat": "tags/v0.1.51",
     "bayeslite": "tags/v0.1.6",
     "bdbcontrib": "tags/v0.1.6",
     "crosscat_tests": "./check.sh",
     "bayeslite_tests": "./check.sh tests shell/tests",
     "bdbcontrib_tests": "./check.sh"},
    {"bayesdb": "0.1.7",  # 2016 Feb 19
     "prereqs": [
         "numpy==1.8.0 --no-cache-dir",
         "pandas==0.17 --no-cache-dir",
         "matplotlib==1.4.3 --no-cache-dir",
         "flaky",
         ],
     "crosscat": "tags/v0.1.51",
     "bayeslite": "tags/v0.1.6",
     "bdbcontrib": "tags/v0.1.7.1",
     "crosscat_tests": "./check.sh",
     "bayeslite_tests": "./check.sh tests shell/tests",
     "bdbcontrib_tests": "./check.sh"},
    {"bayesdb": "0.1.8", # 2016 May 16
     "prereqs": [
         "numpy==1.11.0 --no-cache-dir",
         "pandas==0.18.1 --no-cache-dir",
         "matplotlib==1.4.3 --no-cache-dir",
         ],
     "crosscat": "tags/v0.1.55",
     "bayeslite": "tags/v0.1.8",
     "bdbcontrib": "tags/v0.1.8",
     "crosscat_tests": "./check.sh",
     "bayeslite_tests": "./check.sh tests shell/tests",
     "bdbcontrib_tests": "./check.sh tests examples/tests",
     }
    ]

PREREQS=["pip --upgrade",
         "setuptools --upgrade",
         "cython --no-cache-dir",
         "numpy --no-cache-dir",
         "scipy --no-cache-dir",
         "pandas --no-cache-dir",
         "sklearn --no-cache-dir",
         "matplotlib --no-cache-dir",
         "ipython==3.2.1",
         "requests",
         "seaborn",
         """bayeslite-apsw --install-option="fetch" --install-option="--sqlite"
                           --install-option="--version=3.9.2" """,
         # For testing:
         "mock", "pytest", "pexpect",
         'pillow --global-option="build_ext" --global-option="--disable-jpeg"',
         "pyzmq", "jupyter", "ipython[notebook]==3.2.1", "runipy",
         ]

def get_options():
    from optparse import OptionParser, OptionGroup
    usage = "build_venv.py /path/to/desired/venv_dir"
    parser = OptionParser(usage=usage)
    parser.add_option("-i", "--install-bayesdb", dest="install_bayesdb",
                      action="store_true", default=False,
                      help="Build the venv to include bayesdb")
    parser.add_option("-y", "--from-pypi", dest="from_pypi",
                      action="store_true", default=False,
                      help=("Install bayesdb from pypi rather than github."
                            " Implies --install-bayesdb."))
    parser.add_option("-t", "--run-tests", dest="run_tests",
                      action="store_true", default=False,
                      help="Run the given version's test suites at end.")
    parser.add_option("-d", "--run-demo", dest="run_demo",
                      action="store_true", default=False,
                      help="Check that bayesdb-demo works at end.")
    parser.add_option("-q", "--quiet", dest="quiet", action="store_true",
                      help="Only warnings and errors, not progress or info.",
                      default=False)

    version_group = OptionGroup(
        parser, "BayesDB Version Options",
        "This script keeps a list of versions that are meant to work together."
        " If you specify some version in that list, then the others default to"
        " the ones meant to work with that version. If any version you wanted"
        " is unlisted, then you must specify all three of cc, bl, and bc.")
    version_group.add_option(
        "--cc", "--crosscat-version", dest="crosscat_version",
        help="E.g.: HEAD, latest, 0.1.41, tags/v0.1.41.", default=None)
    version_group.add_option(
        "--bl", "--bayeslite-version", dest="bayeslite_version",
        help="E.g.: HEAD, latest, 0.1.6, tags/v0.1.6", default=None)
    version_group.add_option(
        "--bc", "--bdbcontrib-version", dest="bdbcontrib_version",
        help="E.g.: HEAD, latest, 0.1.6, tags/v0.1.6", default=None)
    version_group.add_option(
        "-v", "--bayesdb-version", dest="bayesdb_version",
        help="E.g.: HEAD, latest, 0.1.6", default="latest")
    parser.add_option_group(version_group)

    prereqs_group = OptionGroup(
        parser, "Prerequisite Version Options",
        "Some packages must be installed before we attempt to build or"
        " test BayesDB. These are currently: " + ", ".join(PREREQS))
    prereqs_group.add_option(
        "-s", "--skip-prereq", dest="skip_prereq", action="append", default=[],
        help=("Skip installing a prerequisite package by this name."
              " If you specify '-s all' then process no prerequisites."))
    prereqs_group.add_option(
        "--pv", "--prerequisite-version", dest="overrides", default=[],
        help=("Override a prerequisite's version. Format is pip's, e.g.:"
              " pandas==0.18, numpy>=1.11 or just the name to ignore any prior"
              " spec."),
        action="append")
    prereqs_group.add_option(
        "-r", "--no-cache-dir", dest="no_cache_dir",
        help=("Force pip to recompile all packages. E.g., with older numpy,"
              " the default binary distributions would otherwise fail."),
        action="store_true", default=False)
    prereqs_group.add_option("-p", "--python", dest="python",
                             help="Path to the python to use.")
    prereqs_group.add_option(
        "-u", "--upgrade", dest="upgrade",
        action="store_true", default=False,
        help=("Ignore all prerequisite package versions, use pypi latest."
              " If the venv_dir already existed, upgrade its packages."))
    parser.add_option_group(prereqs_group)

    (opts, args) = parser.parse_args()
    if opts.quiet:
        import io
        opts.stdout=io.BytesIO()
    else:
        opts.stdout=sys.stdout
    if 'all' in opts.skip_prereq:
        opts.skip_prereq = r'.*'
    venv_dir = args
    if 1 == len(args):
        venv_dir = args[0]
        if venv_dir[0] != "/":
            venv_dir = os.path.join(os.getcwd(), venv_dir)

    if opts.from_pypi:
        opts.install_bayesdb = True
    assert opts.install_bayesdb or not opts.run_demo, \
        "Cannot run the demo unless bayesdb gets installed (-i)."

    return (opts, venv_dir)

def check_virtualenv():
  assert outputof("which pip"), "Need pip to download dependencies."
  assert outputof("which virtualenv"), "You may need to pip install virtualenv"

def check_git():
  assert outputof("git --version"), "Need git to continue."

def make_venv_dir(venv_dir, options):
    parent = os.path.dirname(venv_dir)
    if parent and not os.path.exists(parent):
        os.mkdir(parent, 0755)
    cmd = "virtualenv"
    if options.python:
        assert os.path.exists(options.python)
        cmd += " --python=%s" % (shellquote(options.python))
    cmd += " " + shellquote(venv_dir)
    run(cmd, stdout=options.stdout)

def install_package(venv_dir, package, options):
    for skip in options.skip_prereq:
        if re.search(r'^%s\b' % (skip,), package) or re.match(skip, package):
            return
    install_options = re.split(r"\s+", package, re.S)
    package = install_options.pop(0)
    cmd="pip install"
    if options.no_cache_dir:
        cmd += " --no-cache-dir --no-binary :all: --force"
    if options.upgrade:
        package = re.sub(r'[^\w-].*', '', package)  # Remove any version spec.
        cmd += " --upgrade"
    pkgre = re.compile(r'^%s\b' % package)
    for override in options.overrides:
        if re.search(pkgre, override):
            install_options = re.split(r"\s+", override, re.S)
            package = install_options.pop(0)
            break
    assert re.match(r'[\w\[\]]+\s*([~!<>=]?=*\s*[\w!*\.+-]+)?', package), \
        "Bad version spec?"
    packagename = re.sub(r'\W.*', '', package)
    cmd = " ".join([cmd, package] + [o for o in install_options if o])
    venv_run(venv_dir, cmd, stdout=options.stdout)

def find_distro_tags(package, version, distros):
    headdefault = distros[-1].copy()
    if version.lower() == "latest":
        return headdefault
    if version.lower() == "head":
        assert BAYESDB_DISTRIBUTIONS[0]["bayesdb"] == "HEAD"
        return BAYESDB_DISTRIBUTIONS[0]
    # Allow /6/ to match "tags/v0.1.6", allow /0.1.6/ to match "tags/v0.1.6",
    # but do not allow /6/ to match "0.1.56".
    versionre = re.compile(r'\bv?%s$' % (version,))

    for distro in reversed(distros):  # Reverse to prefer later versions.
        if package in distro and re.search(versionre, distro[package]):
            return distro
    # If the requested version isn't there, assume we want latest for others:
    headdefault[package] = version
    return headdefault

def find_versions(options):
    specified = {}
    distro = BAYESDB_DISTRIBUTIONS[-1].copy()
    if options.crosscat_version:
        distro = find_distro_tags(
            "crosscat", options.crosscat_version, BAYESDB_DISTRIBUTIONS)
        specified["crosscat"] = distro["crosscat"]
        specified["crosscat_tests"] = distro["crosscat_tests"]
    if options.bayeslite_version:
        distro = find_distro_tags(
            "bayeslite", options.bayeslite_version, BAYESDB_DISTRIBUTIONS)
        specified["bayeslite"] = distro["bayeslite"]
        specified["bayeslite_tests"] = distro["bayeslite_tests"]
    if options.bdbcontrib_version:
        distro = find_distro_tags(
            "bdbcontrib", options.bdbcontrib_version, BAYESDB_DISTRIBUTIONS)
        specified["bdbcontrib"] = distro["bdbcontrib"]
        specified["bdbcontrib_tests"] = distro["bdbcontrib_tests"]
    if options.bayesdb_version:
        distro = find_distro_tags(
            "bayesdb", options.bayesdb_version, BAYESDB_DISTRIBUTIONS)
    for k, v in distro.iteritems():
        if k not in specified:
            specified[k] = v
    assert set(["crosscat", "bayeslite", "bdbcontrib"]).issubset(specified)
    return specified

def install_prereqs(venv_dir, versions, options):
    to_install = PREREQS[:]
    if "prereqs" in versions:
        for prereq in versions["prereqs"]:
            found = False
            for i, prior in enumerate(to_install):
                package = re.search(r'^([\w-]+)', prior).group(1)
                if prereq.startswith(package):
                    to_install[i] = prereq
                    found = True
                    break
            if not found:
                to_install.append(prereq)
    for prereq in to_install:
        install_package(venv_dir, prereq, options)

def get_bayesdb(venv_dir, versions, options):
    for package in ("crosscat", "bayeslite", "bdbcontrib"):
        pdir = os.path.join(venv_dir, package)
        need_repo = (options.run_tests or not options.from_pypi or
                     not re.search(r'^tags', versions[package]))
        if need_repo:
            check_git()
            if os.path.exists(pdir):
                run("cd -- %s && git checkout master && git pull" % (pdir,),
                    stdout=options.stdout)
            else:
                run("git clone https://github.com/probcomp/%s %s" %
                    (package, shellquote(pdir)),
                    stdout=options.stdout)
            versions['have_repo_for_'+package] = True
        if need_repo and versions[package] != "HEAD":
            venv_run(venv_dir,
                     "cd -- %s && git checkout %s" % (
                         pdir, shellquote(versions[package])),
                     stdout=options.stdout)
        if options.from_pypi and re.search(r'^tags', versions[package]):
            pypi_version = re.sub(r'.*v', '', versions[package])
            install_package(venv_dir, package+"=="+pypi_version, options)
        elif need_repo and options.install_bayesdb:
            venv_run(venv_dir,
                     "cd -- %s && pip install ." % (pdir,),
                     stdout=options.stdout)
        else:
            pass # Not requesting installation is fine.
    return versions

def requested_testing(venv_dir, options, versions):
    if options.run_tests:
        pythenvs = ""
        for package in ("crosscat", "bayeslite", "bdbcontrib"):
            if ('have_repo_for_'+package in versions and
                package+'_tests' in versions):
                pdir = os.path.join(venv_dir, package)
                venv_run(
                    venv_dir,
                    "cd -- %s && %s %s" % (pdir, pythenvs,
                                           versions[package + "_tests"]),
                    stdout=options.stdout)
                if not options.install_bayesdb and not options.from_pypi:
                    pythenvs += ' ' + os.path.join(pdir, "pythenv.sh")
    if options.run_demo:
        venv_run(venv_dir, "bayesdb-demo --version", stdout=options.stdout)
        venv_run(venv_dir, "bayesdb-demo --help", stdout=options.stdout)
        demodir = os.path.join(venv_dir, "bdb-demo")
        optpath = os.path.join(demodir, "bayesdb-session-capture-opt.txt")
        if os.path.exists(demodir):
            shutil.rmtree(demodir)
        os.makedirs(demodir)
        with open(optpath, "w") as optfile:
            optfile.write("False\n")
        venv_run(venv_dir,
                 "cd -- %s && bayesdb-demo --runipy --destination ." %
                 (shellquote(demodir),),
                 stdout=options.stdout)
        shutil.rmtree(demodir)


def success_message(venv_dir, options):
    if options.quiet:
        return
    print """Installed into %s!

Next steps:
  source $venv_dir/bin/activate
Then you can run the demo:
  bayesdb-demo
  bayesdb-demo --help
Or you can start a notebook, and import bayeslite or bdbcontrib.
  Pay special attention to bdbcontrib.recipes.quickstart and please
  do set the session_capture_name with your info.

NOTE: This new virtualenv will not work if you move or rename it.
Please also subscribe to bayesdb-community@lists.csail.mit.edu. Thanks!
""" % (venv_dir,)

def build_venv_by_options(opts, venv_dir):
    assert venv_dir, (str(parser.print_help())[:0] +
        "Please specify a destination virtualenv path.")
    assert isinstance(venv_dir, str), (str(parser.print_help())[:0] +
        "Need exactly one path argument.")
    check_python(opts.python)
    check_virtualenv()
    make_venv_dir(venv_dir, opts)
    versions = find_versions(opts)
    install_prereqs(venv_dir, versions, opts)
    versions = get_bayesdb(venv_dir, versions, opts)
    requested_testing(venv_dir, opts, versions)
    success_message(venv_dir, opts)

def main():
    (opts, venv_dir) = get_options()
    build_venv_by_options(opts, venv_dir)


if __name__ == "__main__":
    main()
