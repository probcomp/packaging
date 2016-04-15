if application "Safari" is not running then
  return "Safari is not running."
end if

tell application "Safari"
  activate
  do shell script "echo osa: Activated Safari."
  set thePage to the text of current tab of the first window
  if thePage does not contain "satellites" then
    do shell script "echo osa: Failed to open ipython?"
    return thePage
  end if
  set theScript to "$(\".item_name:contains(satellites)\")[0].click();"
  do JavaScript theScript in current tab of first window
  do shell script "echo osa: Waiting for the satellites folder to open."
  delay 10

  set thePage to the text of current tab of the first window
  if thePage does not contain "Satellites" then
    do shell script "echo osa: Failed to open satellites dir?"
    return thePage
  end if
  set theScript to "location.href=$('a[href*=\"Satellites.ipynb\"]')[0].href;"
  do JavaScript theScript in current tab of first window
  do shell script "echo osa: Waiting for the notebook to open."
  delay 10

  set thePage to the text of current tab of the first window
  if thePage does not contain "Union of Concerned Scientists" then
    do shell script "echo osa: Failed to open the notebook."
    return thePage
  end if

  do shell script "echo osa: Waiting for the kernel to start."
  delay 10
  do JavaScript "IPython.notebook.execute_all_cells();" in current tab of the first window
end tell
do shell script "echo osa: Opened and sent run command to the notebook."
