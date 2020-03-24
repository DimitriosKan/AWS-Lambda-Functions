import boto3
import time

rds_cli = boto3.client('rds')
rds_response = rds_cli.describe_db_instances()
available_rds = {}
single_rds = {}

for i in rds_response['DBInstances']:
    available_rds[i['DBInstanceIdentifier']] = i['DBInstanceArn']

def check_if_up(key):
    single_rds_response = rds_cli.describe_db_instances(
            DBInstanceIdentifier=key
        )
    
    for i in single_rds_response['DBInstances']:
        return i['DBInstanceStatus']

while True:
    all_status = []
    print ('Checking state:')
    for key in available_rds:
        value = check_if_up(key)
        if value != 'available' or 'stopped':
            print (f'{key}: {value}')
            all_status.append(f"{value}")
        elif value == 'available' or 'stopped':
            print (f'Instance is {value}')
            all_status.append(f"{value}")
        else:
            print ('failed ...')
    if all(x == 'available' for x in all_status):
        print ('Loop complete !')
        break
    elif all(x == 'stopped' for x in all_status):
        print ('Loop complete !')
        break
    else:
        time.sleep(45)
        print ()
        continue
        print ('I am being rudely skipped')