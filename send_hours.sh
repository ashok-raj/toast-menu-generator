#!/bin/bash
cd /home/araj/work/ChennaiMasala/toast-menu-generator/

# Use python3 if available, fall back to python
PYTHON=$(command -v python3 || command -v python)

# Get the full output
output=$($PYTHON emptime.py -t -S)

# Extract the subject line
subject=$(echo "$output" | grep "TIME LOG SUMMARY" | head -1)

if [[ "$1" == "--dry-run" ]]; then
    echo "Subject: $subject"
    echo "$output"
else
    # Send email with subject and body
    echo "$output" | mutt -F /home/araj/.mutt/gmail-cm-payroll -s "$subject" \
        chennaimasalapayroll@gmail.com, sumathi@chennaimasala.net
fi
