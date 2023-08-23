#!/usr/bin/env python3
"""
# Purpose: For a Google Drive User(s), show all drive file ACLs for files shared with selected users or all users in selected domains.
# Note: This script can use Basic or Advanced GAM:
#	https://github.com/GAM-team/GAM
#	https://github.com/taers232c/GAMADV-XTD3
# Customize: Set USER_LIST and DOMAIN_LIST.
# Python: Use python or python3 below as appropriate to your system; verify that you have version 3
#  $ python -V   or   python3 -V
#  Python 3.x.y
# Usage:
# 1: Get ACLs for all files, if you don't want all users, replace all users with your user selection in the command below
#  $ Basic: gam all users print filelist id title permissions owners mimetype > filelistperms.csv
#  $ Advanced: gam config auto_batch_min 1 redirect csv ./filelistperms.csv multiprocess all users print filelist fields id,title,permissions,owners.emailaddress,mimetype pm type user notrole owner em pmfilter
# 2: From that list of ACLs, output a CSV file with headers "Owner,driveFileId,driveFileTitle,mimeType,permissionId,role,emailAddress"
#    that lists the driveFileIds and permissionIds for all ACLs with the desired users
#    (n.b., driveFileTitle, mimeType, role, and emailAddress are not used in the next step, they are included for documentation purposes)
#  $ python3 GetSharedWithUserDriveACLs.py filelistperms.csv deleteperms.csv
# 3: Inspect deleteperms.csv, verify that it makes sense and then proceed
# 4: If desired, delete the ACLs
#  $ gam csv ./deleteperms.csv gam user "~Owner" delete drivefileacl "~driveFileId" "~permissionId"
"""

import csv
import re
import sys

FILE_NAME = 'name'
ALT_FILE_NAME = 'title'

# You can operate on specific users or specific domains or operate on all users in all domains.
# For all users in all domains, set USER_LIST = [] and DOMAIN_LIST = []

# Substitute your specific user(s) in the list below, e.g., USER_LIST = ['user1@domain.com',] USER_LIST = ['user1@domain.com', 'user2@domain.com',]
# The list should be empty if you're only specifiying domains in DOMAIN_LIST, e.g. USER_LIST = []
USER_LIST = ['ashok.shenoy@salesforce.com','sajid.nadeem@salesforce.com','svoinorosky@salesforce.com','kagnihotri@salesforce.com','amul.shah@salesforce.com','wbalbal@salesforce.com','orebahi@salesforce.com','naoussar@salesforce.com','kashif.ali@salesforce.com','kaityaich@salesforce.com','cbentaleb@salesforce.com','devang.shah@salesforce.com','ozaineb@salesforce.com','znaji@salesforce.com','mmiras@salesforce.com','kevin.johnson@salesforce.com','rhoulton@salesforce.com','samantha.partridge@salesforce.com','andrew.patterson@salesforce.com']
# Substitute your specific domain(s) in the list below if you want all users in the domain, e.g., DOMAIN_LIST = ['domain.com',] DOMAIN_LIST = ['domain1.com', 'domain2.com',]
# The list should be empty if you're only specifiying users in USER_LIST, e.g. DOMAIN__LIST = []
DOMAIN_LIST = []

QUOTE_CHAR = '"' # Adjust as needed
LINE_TERMINATOR = '\n' # On Windows, you probably want '\r\n'

PERMISSIONS_N_TYPE = re.compile(r"permissions.(\d+).type")

if (len(sys.argv) > 2) and (sys.argv[2] != '-'):
  outputFile = open(sys.argv[2], 'w', encoding='utf-8', newline='')
else:
  outputFile = sys.stdout
outputCSV = csv.DictWriter(outputFile, ['Owner', 'driveFileId', 'driveFileTitle', 'mimeType',
                                        'permissionId', 'role', 'emailAddress'],
                           lineterminator=LINE_TERMINATOR, quotechar=QUOTE_CHAR)
outputCSV.writeheader()

if (len(sys.argv) > 1) and (sys.argv[1] != '-'):
  inputFile = open(sys.argv[1], 'r', encoding='utf-8')
else:
  inputFile = sys.stdin

for row in csv.DictReader(inputFile, quotechar=QUOTE_CHAR):
  for k, v in iter(row.items()):
    mg = PERMISSIONS_N_TYPE.match(k)
    if mg and v == 'user':
      permissions_N = mg.group(1)
      if row.get(f'permissions.{permissions_N}.deleted') == 'True':
        continue
      emailAddress = row[f'permissions.{permissions_N}.emailAddress']
      domain = row[f'permissions.{permissions_N}.domain']
      if ((row[f'permissions.{permissions_N}.role'] != 'owner') and
          ((not USER_LIST and not DOMAIN_LIST) or
           (USER_LIST and emailAddress in USER_LIST) or
           (DOMAIN_LIST and domain in DOMAIN_LIST))):
        outputCSV.writerow({'Owner': row['owners.0.emailAddress'],
                            'driveFileId': row['id'],
                            'driveFileTitle': row.get(FILE_NAME, row.get(ALT_FILE_NAME, 'Unknown')),
                            'mimeType': row['mimeType'],
                            'permissionId': f'id:{row[f"permissions.{permissions_N}.id"]}',
                            'role': row[f'permissions.{permissions_N}.role'],
                            'emailAddress': emailAddress})

if inputFile != sys.stdin:
  inputFile.close()
if outputFile != sys.stdout:
  outputFile.close()
