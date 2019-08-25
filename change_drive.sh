#!/bin/bash

###############################################################################
#
# change_drive.sh
# Stephen Zhao

######### UTIL ################################################################

szs_change_drive__debug() {
  if [[ -n "$SZS_G__DEBUG_MODE" && "$SZS_G__DEBUG_MODE" == 1 ]]; then
    echo >&2 "[DBUG][change_drive] $@"
  fi
}

szs_change_drive__warning() {
  echo >&2 "[WARN][change_drive] $@"
}


######### MAIN ################################################################

szs_change_drive__usage() {
  echo "usage: source change_drive.sh <drive_letter>"
}

szs_change_drive__hint() {
    echo >&2 "Try 'change_drive.sh -h' for more information"
}

szs_change_drive__main() {
  if [[ $# -ne 1 ]]; then
    echo >&2 "Incorrect number of parameters"
    szs_change_drive__hint
    return 1
  fi
  if [[ $1 == "-h" ]]; then
    szs_change_drive__usage
    return 0
  fi
  if [[ ! -d "/mnt/$1" ]]; then
    echo >&2 "Invalid drive letter"
    szs_change_drive__hint
    return 1
  fi

  new_drive=$1
  curr_dir="$(pwd)"
  if grep -E "^/mnt/.+/" <<< "$curr_dir" >/dev/null; then
    old_drive=$(grep -Po "^/mnt/\K[^/]+" <<< "$curr_dir")
    if [[ "$old_drive" == "$new_drive" ]]; then
      return 0
    else
      echo "$curr_dir" > "/tmp/szs_change_drive__drive_$old_drive"
    fi
  fi

  if [[ -f "/tmp/szs_change_drive__drive_$new_drive" ]]; then
    cd $(cat "/tmp/szs_change_drive__drive_$new_drive")
  else
    cd "/mnt/$new_drive"
  fi

  return 0
}


szs_change_drive__main $@