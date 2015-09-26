if application "Safari" is not running then
	return "Safari is not running."
end if

tell application "Safari"
	activate
  set thePage to the text of current tab of the first window
	if thePage does not contain "Satellites" then
    return thePage
  end if
	set theScript to "document.getElementsByClassName('item_link')[0].children[0].click();"
	do JavaScript theScript in current tab of first window
	delay 3
  set thePage to the text of current tab of the first window
	if thePage does not contain "Union of Concerned Scientists" then
    return thePage
  end if
	do JavaScript "IPython.notebook.execute_all_cells();" in current tab of the first window
	delay 240
  set thePage to the text of current tab of the first window
  return thePage
end tell
