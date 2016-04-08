# coding=utf-8

import re
import os
import sys
import time
from shell_utils import run, shellquote, outputof, echo

DEBUGGING=False
HOMEDIR="/Users/test"
SCRIPTSDIR=os.path.join(HOMEDIR, "Desktop")
MOUNTDIR=os.path.join(HOMEDIR, "Desktop")
DOCSDIR=os.path.join(HOMEDIR, "Documents")
OPTFILE=os.path.join(HOMEDIR, "bayesdb-session-capture-opt.txt")

def clean_for_test():
  run("osascript %s/close-the-notebook.scpt || true" % (SCRIPTSDIR,))
  if not DEBUGGING:
    run("killall Safari || true")
    run("killall python2.7 || true")
    run("killall Terminal || true")
    run("/bin/ls %s" % (MOUNTDIR,))
    run("/bin/rm -fr %s/Apo*y || true" % (MOUNTDIR,))
    run("/bin/ls %s" % (DOCSDIR,))
    run("/bin/rm -fr %s/* || true" % (DOCSDIR,))

def check_app(app_location, output_path):
  print "check_app(%r, %r)" % (app_location, output_path)
  run("open %s" % (shellquote(app_location),))
  with open(OPTFILE, "w") as optfile:
    optfile.write("False\n")
  time.sleep(30)
  run("osascript -e 'tell application \"Safari\" to activate'")
  run("osascript %s/run-the-notebook.scpt" % (SCRIPTSDIR,))
  result = None
  count = None
  start_time = time.time()
  while not count:
    time.sleep(20)
    result = outputof(
      "osascript %s/grab-safari-tab-contents.scpt" % (SCRIPTSDIR,))
    count = check_result(app_location, result)
    elapsed = time.time() - start_time
    echo("%d seconds elapsed." % (elapsed,))
    assert elapsed < 1200
  echo("That took less than %d wall-clock seconds" % (elapsed,))
  with open(output_path, "w") as outfile:
    print "Writing result [%r] for [%r]." % (output_path, app_location)
    outfile.write(result)
  assert count and count > 10, "%s\n%s" % (app_location, result)
  return result

def run_tests(name):
  clean_for_test()
  run("hdiutil detach /Volumes/Bayeslite || true")
  run("hdiutil attach '%s/%s'" % (MOUNTDIR, name,))
  bname = re.sub(r'\.dmg$', '', name)
  assert bname != name
  check_app("/Volumes/Bayeslite/%s.app" % bname,
            os.path.join(name + ".read-only.out"))
  clean_for_test()
  weirdcharsdir = u"%s/Apo\x27s 1\x22 trophy" % (MOUNTDIR,)
  run("mkdir -p %s" % shellquote(weirdcharsdir))
  run("cp -R /Volumes/Bayeslite/%s.app %s/%s.app" %
           (bname, shellquote(weirdcharsdir), bname))
  run("hdiutil detach /Volumes/Bayeslite")
  check_app(os.path.join(weirdcharsdir, bname + ".app"),
            os.path.join(name + ".weirdchars.out"))
  run("hdiutil detach /Volumes/Bayeslite || true")
  if not DEBUGGING:
    run("/bin/rm -f %s/Bayeslite*.dmg || true" % (MOUNTDIR,))
  clean_for_test()

def check_result(name, contents):
  print "check_result(%r, ...)" % (name)
  opened = None
  count = 0
  for line in contents.split('\n'):
    match = re.search(r'^In\D+([\d*]+)\]:$', line)
    if match:
      opened = match.group(1)
    else:
      match = re.search(r'^Out\s*\[([\d*]+)\]:', line)
      if match:
        if opened != match.group(1):
          echo("Opened not closed [%r] != [%r] for %s" %
             (opened, match.group(0), name))
        else:
          count += 1
          opened = None
  if opened is not None:
    echo("Opened is not None at end: %s for %s" % (opened, name))
    return False
  return count

def main():
    name = sys.argv[1]
    run_tests(name)

if __name__ == "__main__":
    main()
