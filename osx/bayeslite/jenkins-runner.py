# This is intended to be run by Jenkins on probcomp.

# Setup includes:  (everything as build@ except where probcomp$ or test$ are specified)
# 1. test@ and build@ users on the mac.
# 2. authorized_keys for jenkins, and mac's configuration to allow ssh.
# 3. XCode on the mac, with command line tools: xcode-select --install
# 4. build added to the _developer group via
#    probcomp$ sudo dscl . append /Groups/_developer GroupMembership build
# 5. Homebrew, python, virtualenv, and boost installed for the user:
#    mkdir homebrew
#    curl -L https://github.com/Homebrew/homebrew/tarball/master | tar xz --strip 1 -C homebrew
#    ./bin/brew update && ./bin/brew doctor
#    ./bin/brew install python boost boost-build
#    ./bin/pip install virtualenv
# 6. The locate database up to date, so the builder can find boost:
#    probcomp$ sudo /usr/libexec/locate.updatedb
# 7. /scratch/dmgs available to Jenkins.
# 8. test@ is configured to Allow Applications from Anywhere (System Preferences > Security)
# 9. test@'s Safari is configured to allow popups. (Safari > Preferences > Security)

import re
import os
import time
from shell_utils import run, shellquote, outputof, echo

HOST = "pcg-osx-test.mit.edu"
HPATH = "/Users/build/homebrew/bin"
SCRATCH = "/scratch/dmgs"
LOCKFILE = os.path.join(SCRATCH, "lock")

def wait_for_lock():
  while os.path.exists(LOCKFILE):
    echo("Waiting for lock", LOCKFILE)
    time.sleep(60)
    if os.path.exists(LOCKFILE):
      with open(LOCKFILE, "r") as lockfile:
        contents = lockfile.read()
      pid = re.sub(r'\D', '', contents)
      if not pid or not os.path.exists('/proc/' + pid):
        echo("Breaking lock", LOCKFILE)
        break  # That process is no longer running. Break the lock.
  with open(LOCKFILE, "w") as lockfile:
    lockfile.write(str(os.getpid()))
  assert os.path.exists(LOCKFILE)
  with open(LOCKFILE, "r") as lockfile:
    assert os.getpid() == int(lockfile.read())

def build_run(cmd):
  run("ssh build@%s %s" % (HOST, shellquote(cmd)))
def build_outputof(cmd):
  return outputof("ssh build@%s %s" % (HOST, shellquote(cmd)))
def test_run(cmd):
  run("ssh test@%s %s" % (HOST, shellquote(cmd)))

def build_dmg():
  run("scp build_dmg.py shell_utils.py build@%s:" % (HOST,))
  build_run('PATH="%s:$PATH" python build_dmg.py' % (HPATH,))
  run("scp build@%s:Desktop/Bayeslite*.dmg %s" % (HOST, SCRATCH))
  name = build_outputof("cd Desktop && ls -t Bayeslite*.dmg | tail -1").strip()
  echo("NAME:", name)
  build_run("/bin/rm -f Desktop/Bayeslite*.dmg")
  return name

def debug_skip_build():
  return outputof("cd %s && ls -t %s | tail -1" % (SCRATCH, "*.dmg")).strip()

def test_dmg(name):
  run("scp *.scpt shell_utils.py test_dmg.py %s test@%s:Desktop/" %
      (os.path.join(SCRATCH, name), HOST))
  test_run("python Desktop/test_dmg.py %s" % name)

def main():
  wait_for_lock()
  try:
    name = build_dmg()
    test_dmg(name)
  finally:
    os.remove(LOCKFILE)

if __name__ == "__main__":
  main()
