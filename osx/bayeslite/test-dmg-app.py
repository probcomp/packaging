# coding=utf-8

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
from build_utils import run, shellquote, outputof

HOST = "pcg-osx-test.mit.edu"
HPATH = "/Users/build/homebrew/bin"
SCRATCH = "/scratch/dmgs"
LOCKFILE = os.path.join(SCRATCH, "lock")

def wait_for_lock():
  while os.path.exists(LOCKFILE):
    time.sleep(60)
    if os.path.exists(LOCKFILE):
      with open(LOCKFILE, "r") as lockfile:
        contents = lockfile.read()
      pid = re.sub(r'\D', '', contents)
      if not os.path.exists('/proc/' + pid):
        break  # That process is no longer running. Break the lock.
  with open(LOCKFILE, "w") as lockfile:
    lockfile.write(str(os.getpid()))
  assert os.path.exists(LOCKFILE)
  with open(LOCKFILE, "r") as lockfile:
    assert os.getpid() == int(lockfile.read())

def build_run(cmd):
  run("ssh build@%s '%s'" % (HOST, shellquote(cmd)))
def build_output(cmd):
  return outputof("ssh build@%s '%s'" % (HOST, shellquote(cmd)))
def test_run(cmd):
  run("ssh test@%s '%s'" % (HOST, shellquote(cmd)))
def test_output(cmd):
  return outputof("ssh test@%s '%s'" % (HOST, shellquote(cmd)))

def build_dmg():
  run("scp build_dmg.py build@%s:" % (HOST,))
  build_run('PATH="%s:\\$PATH" python build_dmg.py' % (HPATH,))
  run("scp build@%s:Desktop/Bayeslite*.dmg %s" % (HOST, SCRATCH))
  name = build_output("cd Desktop && ls -t Bayeslite*.dmg | tail -1")
  print "NAME:", name
  return name

def clean_for_test(eject=True):
  test_run("osascript -e 'tell application \"Safari\" to close every window'" +
           " || true")
  test_run("killall Safari || true")
  test_run("killall python2.7 || true")
  test_run("killall Terminal || true")
  if eject:
    test_run("hdiutil detach /Volumes/Bayeslite || true")
    build_run("/bin/rm -f Desktop/Bayeslite*.dmg")

def get_app_output(app_location, output_path):
  test_run("open '%s'" % (app_location,))
  time.sleep(45)
  test_run("osascript -e 'tell application \"Safari\" to activate'")
  result = test_output("osascript check-safari.scpt")
  with(output_path, "w") as outfile:
    outfile.write(result)
  return result

def run_tests(name):
  clean_for_test()
  run("scp %s test@%s:" % (os.path.join(SCRATCH, name), HOST))
  test_run("hdiutil attach '%s'" % (name,))
  bname = re.sub(r'.app$', '', name)
  read_only_result = get_app_output(
    "/Volumes/Bayeslite/%s.app" % bname,
    os.path.join(SCRATCH, name + ".read-only.out"))
  clean_for_test(eject=False)
  weirdcharsdir = "~/Desktop/Apo's 1\" trõpηe".decode('utf-8')
  test_run("cp -R /Volumes/Bayeslite/%s.app '%s/'" %
           (bname, shellquote(weirdcharsdir.encode('utf-8'))))
  test_run("hdiutil detach /Volumes/Bayeslite")
  weirdchars_result = get_app_output(
    os.path.join(weirdcharsdir, bname + ".app"),
    os.path.join(SCRATCH, name + ".weirdchars.out"))
  clean_for_test()
  return (read_only_result, weirdchars_result)

def check_result(name, contents):
  opened = None
  count = 0
  for line in contents:
    match = line.search(r'^In\s*\[(\d+)\]:')
    if match:
      assert opened is None, name
      opened = match.group(0)
      count += 1
    else:
      match = line.search(r'^Out\s*\[(\d)\]:')
      if match:
        assert opened == match.group(0), name
        opened = None
  assert opened is None, name
  assert count > 10, name

def main():
  wait_for_lock()
  (ro, wc) = (None, None)
  try:
    name = build_dmg()
    (ro, wc) = run_tests(name)
  finally:
    os.remove(LOCKFILE)
  check_result("read-only", ro)
  check_result("weird-chars", wc)

if __name__ == "__main__":
  main()
