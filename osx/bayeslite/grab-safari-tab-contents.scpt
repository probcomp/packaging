if application "Safari" is not running then
  return "Safari is not running."
end if

tell application "Safari"
  set thePage to the text of current tab of the first window
  return thePage
end tell
