if application "Safari" is running then
        tell application "Safari"
                activate
                set theWindows to windows as list
                repeat with w from (count of theWindows) to 1 by -1
                        set theWindow to window (w - 1)
                        set theTabs to every tab in theWindow as list
                        repeat with t from 1 to (count of theTabs)
                                close current tab of window (w - 1)
                        end repeat
                end repeat
        end tell
        quit application "Safari"
end if
