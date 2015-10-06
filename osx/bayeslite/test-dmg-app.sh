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

set -e
set -x

host=pcg-osx-test.mit.edu
hpath=/Users/build/homebrew/bin

# TODO(gremio): Test that the .app works correctly if copied from the readonly volume to a
# local directory with spaces and an apostrophe, and mixed case.
# badchar_dir="/Users/test/This account's temp"

lockfile=/scratch/dmgs/lock
while [ -e $lockfile ]; do
    sleep 60
    if [ -e $lockfile ]; then
        set +e
        pid=`cat $lockfile | sed 's/[^0-9]//g'`
        if [ -n "$pid" ]; then
            running=`/bin/ps -p $pid | grep $pid`
            if [ -z "$running" ]; then
                /bin/rm -f $lockfile
            fi
        fi
        set -e
    fi
done
echo $$ > $lockfile

# Build the dmg
# =============

scp build_dmg.py build@$host:
ssh build@$host "PATH=\"$hpath:\$PATH\" python build_dmg.py"
scp build@$host:Desktop/Bayeslite*.dmg /scratch/dmgs/
name=$(ssh build@$host "(cd Desktop && ls Bayeslite*.dmg | tail -1)")
echo "NAME: [$name]"

# Clean the test machine before trying to run
# ===========================================
ssh test@$host "osascript -e 'tell application \"Safari\" to close every window'" || true
ssh test@$host "killall Safari" || true
ssh test@$host "killall python2.7" || true
ssh test@$host "killall Terminal" || true
ssh test@$host "hdiutil detach /Volumes/Bayeslite" || true

# Run the test and collect its output
# ===================================
scp /scratch/dmgs/$name test@$host:
ssh test@$host "hdiutil attach $name"
bname=$(basename $name .dmg)
ssh test@$host "open /Volumes/Bayeslite/$bname.app"
sleep 45
ssh test@$host "osascript -e 'tell application \"Safari\" to activate'"
scp check-safari.scpt test@$host:
outfile=/scratch/dmgs/$name.out
ssh test@$host "osascript check-safari.scpt" > $outfile
# $outfile now has the fully executed Satellites.ipynb contents (or however far they got).

# Clean up
# ========
ssh test@$host "osascript -e 'tell application \"Safari\" to close every window'"
ssh test@$host "killall Safari"
ssh test@$host "killall python2.7"
ssh test@$host "killall Terminal"

weirdcharsdir="~/Desktop/Apo's trõpηe"

ssh test@$host "cp -R /Volumes/Bayeslite/$bname.app '$weirdcharsdir/'"
ssh test@$host "hdiutil detach /Volumes/Bayeslite"
ssh build@$host "/bin/rm -f Desktop/Bayeslite*.dmg"
ssh test@$host "open '$weirdcharsdir/$bname.app'"
sleep 45
ssh test@$host "osascript -e 'tell application \"Safari\" to activate'"
scp check-safari.scpt test@$host:
weird_outfile=/scratch/dmgs/$name-weirdchars.out
ssh test@$host "osascript check-safari.scpt" > $weird_outfile
# $outfile now has the fully executed Satellites.ipynb contents (or however far they got).

# Final cleanup
ssh test@$host "osascript -e 'tell application \"Safari\" to close every window'"
ssh test@$host "killall Safari"
ssh test@$host "killall python2.7"
ssh test@$host "killall Terminal"

# Others can go ahead now:
/bin/rm -f $lockfile

# Check the output
# ================
# The last two lines (tail -2) after the egrep should be:
# In [18]:
# Out[18]:
# or similar, perhaps with different numbers.
# uniq -c counts those. If the result starts with 2, then they were the same, which is good.
# If they're not the same, the set -e at the top should crash this, and make Jenkins fail.
egrep '^(In|Out).?\[[0-9][0-9]*\]:' $outfile | tail -2 | sed 's/[^0-9]//g' | uniq -c | sed 's/ //g' | egrep '^2[0-9][0-9]'
egrep '^(In|Out).?\[[0-9][0-9]*\]:' $weird_outfile | tail -2 | sed 's/[^0-9]//g' | uniq -c | sed 's/ //g' | egrep '^2[0-9][0-9]'


set +x
