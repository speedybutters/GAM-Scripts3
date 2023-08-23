#!/usr/bin/env python3
"""
# Purpose: Show all drive file ACLs for Team Drive files shared with selected users or all users in selected domains.
# Note: This script requires Advanced GAM:
#	https://github.com/taers232c/GAMADV-XTD3
# Customize: Set USER_LIST, DOMAIN_LIST, NON_INHERITED_ACLS_ONLY
# Python: Use python or python3 below as appropriate to your system; verify that you have version 3
#  $ python -V   or   python3 -V
#  Python 3.x.y
# Usage:
# For all Team Drives, start at step 1; For Team Drives selected by user/group/OU, start at step 7
# All Team Drives
# 1: Get all Team Drives.
#  $ gam redirect csv ./TeamDrives.csv print teamdrives fields id,name
# 2: Get ACLs for all Team Drives
#  $ gam redirect csv ./TeamDriveACLs.csv multiprocess csv ./TeamDrives.csv gam print drivefileacls "~id" fields emailaddress,role,type
# 3: Customize GetTeamDriveOrganizers.py for this task:
#    Set DOMAIN_LIST as required
#    Set ONE_ORGANIZER = True
#    Set SHOW_GROUP_ORGANIZERS = False
#    Set SHOW_USER_ORGANIZERS = True
# 4: From that list of ACLs, output a CSV file with headers "id,name,organizers"
#    that shows the organizers for each Team Drive
#  $ python3 GetTeamDriveOrganizers.py TeamDriveACLs.csv TeamDrives.csv TeamDriveOrganizers.csv
# 5: Get ACLs for all team drive files
#  $ gam config csv_input_row_filter "organizers:regex:^.+$" redirect csv ./filelistperms.csv multiprocess csv ./TeamDriveOrganizers.csv gam user "~organizers" print filelist select teamdriveid "~id" fields teamdriveid,id,name,permissions,mimetype
# 6: Go to step 11
# Selected Team Drives
# 7: If you want Team Drives for a specific set of organizers, replace <UserTypeEntity> with your user selection in the command below
#  $ gam redirect csv ./AllTeamDrives.csv <UserTypeEntity> print teamdrives role organizer fields id,name
# 8: Customize DeleteDuplicateRows.py for this task:
#    Set ID_FIELD = 'id'
# 9: Delete duplicate Team Drives (some may have multiple organizers).
#  $ python3 DeleteDuplicateRows.py ./AllTeamDrives.csv ./TeamDrives.csv
# 10: Get ACLs for all team drive files
#  $ gam redirect csv ./filelistperms.csv multiprocess csv ./TeamDrives.csv gam user "~User" print filelist select teamdriveid "~id" fields teamdriveid,id,name,permissions,mimetype
# Common code
# 11: From that list of ACLs, output a CSV file with headers "Owner,driveFileId,driveFileTitle,mimeType,permissionId,role,emailAddress"
#    that lists the driveFileIds and permissionIds for all ACLs with the desired users
#    (n.b., driveFileTitle, mimeType, role, and emailAddress are not used in the next step, they are included for documentation purposes)
#  $ python3 GetSharedWithUserTeamDriveACLs.py filelistperms.csv deleteperms.csv
# 12: Inspect deleteperms.csv, verify that it makes sense and then proceed
# 13: If desired, delete the ACLs
#  $ gam csv ./deleteperms.csv gam user "~Owner" delete drivefileacl "~driveFileId" "~permissionId"
"""

import csv
import re
import sys

FILE_NAME = 'name'
ALT_FILE_NAME = 'title'

# You can ooperate on specific users or specific domains or operate on all users in all domains.
# For all users in all domains, set USER_LIST = [] and DOMAIN_LIST = []

# Substitute your specific user(s) in the list below, e.g., USER_LIST = ['user1@domain.com',] USER_LIST = ['user1@domain.com', 'user2@domain.com',]
# The list should be empty if you're only specifiying domains in DOMAIN_LIST, e.g. USER_LIST = []
USER_LIST = ['ashok.shenoy@salesforce.com','sajid.nadeem@salesforce.com','svoinorosky@salesforce.com','kagnihotri@salesforce.com','amul.shah@salesforce.com','wbalbal@salesforce.com','orebahi@salesforce.com','naoussar@salesforce.com','kashif.ali@salesforce.com','kaityaich@salesforce.com','cbentaleb@salesforce.com','devang.shah@salesforce.com','ozaineb@salesforce.com','znaji@salesforce.com','mmiras@salesforce.com','kevin.johnson@salesforce.com','rhoulton@salesforce.com','samantha.partridge@salesforce.com','andrew.patterson@salesforce.com']
# Substitute your specific domain(s) in the list below if you want all users in the domain, e.g., DOMAIN_LIST = ['domain.com',] DOMAIN_LIST = ['domain1.com', 'domain2.com',]
# The list should be empty if you're only specifiying users in USER_LIST, e.g. DOMAIN__LIST = []
DOMAIN_LIST = []

# Specify whether only non-inherited ACLs should be output; inherited ACLs can't be deleted
NON_INHERITED_ACLS_ONLY = True

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
      if NON_INHERITED_ACLS_ONLY and str(row.get(f'permissions.{permissions_N}.permissionDetails.0.inherited', False)) == 'True':
        continue
      emailAddress = row[f'permissions.{permissions_N}.emailAddress']
      domain = row[f'permissions.{permissions_N}.domain']
      if ((row[f'permissions.{permissions_N}.role'] != 'owner') and
          ((not USER_LIST and not DOMAIN_LIST) or
           (USER_LIST and emailAddress in USER_LIST) or
           (DOMAIN_LIST and domain in DOMAIN_LIST))):
        outputCSV.writerow({'Owner': row['Owner'],
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
