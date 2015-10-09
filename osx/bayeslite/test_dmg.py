# coding=utf-8

import re
import os
import sys
import time
from shell_utils import run, shellquote, outputof, echo

def clean_for_test():
  run("osascript -e 'tell application \"Safari\" to close every window' ||true")
  run("killall Safari || true")
  run("killall python2.7 || true")
  run("killall Terminal || true")
  run("/bin/rm -fr /Users/test/Desktop/Apo*y || true")

def check_app(app_location, output_path):
  run("open %s" % (shellquote(app_location),))
  time.sleep(45)
  run("osascript -e 'tell application \"Safari\" to activate'")
  run("osascript /Users/test/Desktop/run-the-notebook.scpt")
  result = None
  count = None
  start_time = time.time()
  while not count:
    time.sleep(20)
    result = outputof(
      "osascript /Users/test/Desktop/grab-safari-tab-contents.scpt")
    count = check_result(app_location, result)
    elapsed = time.time() - start_time
    echo("%d seconds elapsed." % (elapsed,))
    assert elapsed < 1200
  echo("That took less than %d wall-clock seconds" % (elapsed,))
  with open(output_path, "w") as outfile:
    outfile.write(result)
  assert count and count > 10, "%s\n%s" % (app_location, result)
  return result

def run_tests(name):
  clean_for_test()
  run("hdiutil detach /Volumes/Bayeslite || true")
  run("hdiutil attach '/Users/test/Desktop/%s'" % (name,))
  bname = re.sub(r'\.dmg$', '', name)
  assert bname != name
  check_app("/Volumes/Bayeslite/%s.app" % bname,
            os.path.join(name + ".read-only.out"))
  clean_for_test()
  weirdcharsdir = u"/Users/test/Desktop/Apo\x27s 1\x22 trophy"
  run("mkdir -p %s" % shellquote(weirdcharsdir))
  run("cp -R /Volumes/Bayeslite/%s.app %s/%s.app" %
           (bname, shellquote(weirdcharsdir), bname))
  run("hdiutil detach /Volumes/Bayeslite")
  check_app(os.path.join(weirdcharsdir, bname + ".app"),
            os.path.join(name + ".weirdchars.out"))
  run("hdiutil detach /Volumes/Bayeslite || true")
  run("/bin/rm -f Desktop/Bayeslite*.dmg || true")
  clean_for_test()

def check_result(name, contents):
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
