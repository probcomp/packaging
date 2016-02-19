# -*- coding: utf-8 -*-
from __future__ import print_function

#   Copyright (c) 2010-2014, MIT Probabilistic Computing Project
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

# Requires boost pre-installed.
# This is slightly special if you want to use Venture. The GNU c++
# compilers use the standard library libstdc++, while Mac's c++
# compiler on Mavericks uses libc++. In order for Venture to build,
# you must build Boost using libstdc++, and then build Venture using
# the same. This can be accomplished by building both Boost and
# Venture using GNU gcc (installed via Homebrew) instead of Mac's
# compiler. The correct version of gcc is set for Venture installation
# in the setup.py file. To install Boost with the correct library,
# call:
#
#    brew install boost --cc=gcc-4.9
#    brew install boost-python --cc=gcc-4.9

# Requires locate to be working, so we can find a pre-installed boost.
# Requires virtualenv pre-installed.
# Requires read access to the listed git repos.
GIT_REPOS = ['crosscat', 'bayeslite', 'bdbcontrib']

# PKG_VERSIONS may be 'head', 'latest', or a comma-delimited list of
# package:version pairs.
PKG_VERSIONS = None
import sys
if len(sys.argv) > 1:
    PKG_VERSIONS = sys.argv[1]

PAUSE_TO_MODIFY = False

import distutils.spawn  # pylint: disable=import-error
import errno
import os
import re
import sys
import stat
import time
import tempfile
import textwrap
import traceback
try:
  from setuptools import setup
except ImportError:
  from distutils.core import setup # pylint: disable=import-error

from shell_utils import run, outputof, venv_run, shellquote, echo

def check_python():
  # Do not specify --python to virtualenv, bc eg python27 is a 32-bit version
  # that will produce a .app that osx will not open.
  # You get errors like:
  #    You can’t open the application “...” because PowerPC applications are no
  #    longer supported.
  # Or less helpfully:
  #    The application “...” can’t be opened.
  # and when investigating:
  #    lipo: can't figure out the architecture type of: ...
  # Instead, use the built-in python by not specifying anything, and get fine
  # results.
  # Rather than merely praying that the built-in python is
  # language-compatible, let's check.
  pyver = outputof('python --version 2>&1')
  assert "Python 2.7" == pyver[:10]

def get_project_version(project_dir):
  here = os.getcwd()
  try:
    os.chdir(project_dir)
    line = outputof('python setup.py --version')
    return line.rstrip()        # Omit trailing newline.
  finally:
    os.chdir(here)

def get_latest_git_annotated_version(project_dir):
  cmd = ('git for-each-ref --sort=\'*authordate\' '
         '--format=\'%(tag)\' refs/tags | tail -1')
  return outputof("cd -- %s && %s" % (shellquote(project_dir), cmd)).rstrip()

def version_dict(build_dir):
  def dir(proj):
    return os.path.join(build_dir, proj)
  if PKG_VERSIONS in (None, 'head', 'HEAD'):
    return dict([(proj, get_project_version(dir(proj))) for proj in GIT_REPOS])
  elif PKG_VERSIONS == 'latest':
    return dict([(proj, get_latest_git_annotated_version(dir(proj)))
                 for proj in GIT_REPOS])
  else:
    return dict([pkg.split(':') for pkg in PKG_VERSIONS.split(',')])

def composite_version(build_dir):
  vdict = version_dict(build_dir)
  if PKG_VERSIONS in (None, 'head', 'HEAD'):
    return '-'.join([proj[:5] + vdict[proj] for proj in GIT_REPOS])
  else:
    return vdict['bdbcontrib']

def do_pre_installs(unused_build_dir, venv_dir):
  echo("Deps for CrossCat")
  boost_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    outputof("mdfind -name mersenne_twister.hpp | "  # no -path option.
             "grep include/boost/random/mersenne_twister.hpp | head -1")))))
  assert os.path.exists(boost_dir), \
    ("We need boost headers already installed for CrossCat: %s" % (boost_dir,))
  echo("BOOST_ROOT=%s" % (shellquote(boost_dir),))
  os.environ["BOOST_ROOT"] = boost_dir
  # If we don't install cython and numpy, crosscat's setup tries and fails:
  venv_run(venv_dir, "pip install --no-cache-dir "
           "cython numpy==1.8.2 matplotlib==1.4.3 scipy")
  venv_run(venv_dir, "pip install --no-cache-dir pandas "
           "--install-option=\"build_ext\"")
  venv_run(venv_dir, "pip install --no-cache-dir bayeslite-apsw "
           "--install-option=\"fetch\" --install-option=\"--sqlite\" "
           "--install-option=\"--version=3.9.2\"")

  # TODO: Auto-sync with packaging/jenkins/prereqs_wrapper.sh or similar.

def do_main_installs(build_dir, venv_dir):
  for project in GIT_REPOS:
    echo("Cloning ", project)
    repodir = os.path.join(build_dir, project)
    run("git clone https://github.com/probcomp/%s.git %s"
        % (shellquote(project), shellquote(repodir)))
  vdict = version_dict(build_dir)
  for project in GIT_REPOS:
    echo("Checking out", project, "version", vdict[project])
    version = vdict[project]
    if re.search('post', version):
      version = 'HEAD'
    repodir = os.path.join(build_dir, project)
    run("cd -- %s && git checkout %s" %
        (shellquote(repodir), shellquote(version)))
    reqfile = os.path.join(repodir, "requirements.txt")
    if os.path.exists(reqfile):
      echo("Installing dependencies for", project)
      venv_run(venv_dir, "pip install -r %s" % (shellquote(reqfile),))
    setupfile = os.path.join(repodir, "setup.py")
    if os.path.exists(setupfile):
      echo("Installing", project, "from", build_dir, "into", venv_dir)
      venv_run(venv_dir, "cd -- %s && pip install ." % (shellquote(repodir),))

def do_post_installs(unused_build_dir, venv_dir):
  # This app's only other dependency:
  venv_run(venv_dir, "pip install jupyter 'ipython[notebook]==3.2.1' runipy")
  venv_run(venv_dir, 'virtualenv --relocatable %s' % (shellquote(venv_dir),))
  # Sadly, that doesn't actually fix the most critical file, the activate script

  # App was prompting people to accept xcode license to use git.
  # No actual need for ipynotebook to check git, so disable it
  # just within the app (per bayeslite/issues/139)
  gitfile = os.path.join(venv_dir, "bin/git")
  with open(gitfile, "w") as gitf:
      gitf.write(textwrap.dedent("""#!/bin/sh
         exit 1  # It is an error for bayeslite to try to use git.
         """))
  os.chmod(gitfile, # Make executable by everyone.
           os.stat(gitfile).st_mode | stat.S_IXUSR | stat.S_IXGRP |
           stat.S_IXOTH)

def fix_python_and_its_path(venv_dir):
  # By default, venv hard links to the python that it was built with,
  # which may be different than the python that we want the client to
  # execute. Let's just assume that on the client, we want to use the
  # generic /System/Library py2.7, rather than a special one.
  sys_python = "/System/Library/Frameworks/Python.framework/Versions/2.7/Python"
  python_dylib_link = os.path.join(venv_dir, ".Python")
  run("ln -fs %s %s" % (shellquote(sys_python), shellquote(python_dylib_link)))

  bin_python = os.path.join(venv_dir, "bin", "python")
  run("rm -f %s" % (shellquote(bin_python),))
  #with open(bin_python, "w") as bp:
  #  bp.write("""#!/bin/bash\nexec -a "$0" /usr/bin/python2.7 ${1+"$@"}\n""")
  #run("chmod a+x %s" % (shellquote(bin_python),))
  run("ln -s /usr/bin/python2.7 %s" % (shellquote(bin_python),))
  os.environ["PYTHONPATH"] = os.path.join(
      venv_dir, "lib/python2.7/site-packages")

def make_venv_truly_relocatable(venv_dir):
  relocable = '''VIRTUAL_ENV=$(dirname -- "$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" && pwd )")\n'''
  new_activate = tempfile.NamedTemporaryFile(delete=False)
  old_activate_path = os.path.join(venv_dir, "bin", "activate")
  with open(old_activate_path, "r") as old_activate:
    for line in old_activate:
      if line[:len("VIRTUAL_ENV=")] == "VIRTUAL_ENV=":
        new_activate.write(relocable)
      else:
        new_activate.write(line)
  new_activate.close()
  run("mv %s %s" %
      (shellquote(new_activate.name), shellquote(old_activate_path)))

def make_starter_script(macos_path):
  starter_script = '''#!/bin/bash

set -e
wd=`dirname -- "$0"`
cd -- "$wd"
wd=`pwd -P`
NAME=`basename -- "$(dirname -- "$(dirname -- "$wd")")" .app`

activate="$wd/venv/bin/activate"
ldpath="$wd/lib"

# Clear any user's PYTHONPATH setting, which may interfere with what
# we need.
unset PYTHONPATH
export PYTHONPATH="$wd/venv/lib/python2.7/site-packages"

source "$activate"
export DYLD_LIBRARY_PATH="$ldpath"
export MPLBACKEND=pdf

# Download and run the examples in someplace writeable:
"$wd/venv/bin/bayesdb-demo" --destination "$HOME/Documents"
'''
  startsh_path = os.path.join(macos_path, "start.sh")
  with open(startsh_path, "w") as startsh:
    startsh.write(starter_script)
  run("chmod +x %s" % (shellquote(startsh_path),))

def make_launcher_script(macos_path, name):
  launcher_script = '''#!/bin/bash

wd=`dirname -- "$0"`
cd -- "$wd"
wd=`pwd -P`

osascript -e '
    on run argv
        set wd to item 1 of argv
        set cmd to "/bin/bash -- " & quoted form of wd & "/start.sh"
        tell application "Terminal" to do script cmd
    end run
' -- "$wd"
'''

  launchsh_path = os.path.join(macos_path, name)
  with open(launchsh_path, "w") as launchsh:
    launchsh.write(launcher_script)
  run("chmod +x %s" % (shellquote(launchsh_path),))

def wrap_as_macos_dir(build_dir, name):
  """Return the dmg root dir inside build_dir, and within that the MacOs dir."""
  dist_dir = os.path.join(build_dir, "dmgroot")
  macos_path = os.path.join(dist_dir, name + ".app", "Contents", "MacOS")
  os.makedirs(macos_path)
  run("/bin/ln -s /Applications %s" % (shellquote(dist_dir),))
  make_starter_script(macos_path)
  make_launcher_script(macos_path, name)
  return dist_dir, macos_path

def basic_sanity_check(venv_dir):
  test_dir = tempfile.mkdtemp('bayeslite-test')
  try:
    venv_run(venv_dir,
             "cd -- %s && bayesdb-demo fetch" % (shellquote(test_dir),))
    venv_run(venv_dir,
             "cd -- %s && "
             "MPLBACKEND=pdf PYTHONPATH=%s runipy %s" %
             (shellquote(test_dir),
              shellquote(os.path.join(venv_dir,
                                      "lib/python2.7/site-packages")),
              "Bayeslite-v*/satellites/Satellites.ipynb"))
  finally:
    run("rm -rf -- %s" % (shellquote(test_dir),))

def pause_to_modify(macos_path):
  if PAUSE_TO_MODIFY and sys.__stdin__.isatty():
    echo("Pausing to let you modify %s before packaging it up." % (macos_path,))
    os.system('read -s -n 1 -p "Press any key to continue..."')

def make_dmg_on_desktop(dist_dir, name):
  dmg_path = os.path.join(os.environ['HOME'], 'Desktop', '%s.dmg' % (name,))
  naming_attempt = 0
  while os.path.exists(dmg_path):
    naming_attempt += 1
    dmg_path = os.path.join(os.environ['HOME'], 'Desktop',
                            "%s (%d).dmg" % (name, naming_attempt))
  run("hdiutil create -volname Bayeslite -format UDBZ -size 1g -srcfolder %s %s"
      % (shellquote(dist_dir), shellquote(dmg_path)))

def main():
  start_time = time.time()
  check_python()

  build_dir = tempfile.mkdtemp(prefix='BayesLite-app-')
  os.chdir(build_dir)
  echo("Building in", build_dir)
  echo("PATH is", os.environ["PATH"])

  venv_dir = os.path.join(build_dir, "venv")
  run('virtualenv %s' % (shellquote(venv_dir),))

  do_pre_installs(build_dir, venv_dir)
  do_main_installs(build_dir, venv_dir)
  do_post_installs(build_dir, venv_dir)
  fix_python_and_its_path(venv_dir)
  make_venv_truly_relocatable(venv_dir)

  name="Bayeslite-%s" % (composite_version(build_dir),)
  (dist_dir, macos_dir) = wrap_as_macos_dir(build_dir, name)
  run("mv -f %s %s" % (shellquote(venv_dir), shellquote(macos_dir)))
  venv_dir = os.path.join(macos_dir, "venv")

  basic_sanity_check(venv_dir)
  pause_to_modify(macos_dir)
  make_dmg_on_desktop(dist_dir, name)
  run("/bin/rm -fr %s" % (shellquote(build_dir),))
  echo("Done. %d seconds elapsed" % (time.time() - start_time,))

if __name__ == "__main__":
    main()
