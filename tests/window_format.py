import boto3
import datetime

rds_cli = boto3.client('rds')
rds_response = rds_cli.describe_db_instances()
available_rds = {}
parsed_times = {}
a_form = '%a:%H:%M- %d %m %Y'
b_form = '%Y-%m-%d %H:%M:%S'

# here I just snip the end bits to get a check date, which will match the current one
def time_addon():
    time_addon = datetime.datetime.now().strftime(a_form).split('-')
    # print (time_addon[1])
    return time_addon[1]

for i in rds_response['DBInstances']:
    available_rds[i['DBInstanceIdentifier']] = [i['DBInstanceArn'], str(i['PreferredMaintenanceWindow'].split('-')[1]).capitalize()]

    # here we format the string so it is comparable with the current date format
    # window_end = str(i['PreferredMaintenanceWindow'].split('-')[0]).capitalize()
    # window_end_date_complete = rds_availability + '-' + time_addon()

# V Tests below V
print ('Available rds:')
print (available_rds)
# /\ Tests above /\

for key in available_rds:
    print ()
    print (f'Working {key} ...')
    rds_arn = available_rds.get(key, 'Not Found !')[0]
    rds_availability = available_rds.get(key, 'Not Found !')[1]

    window_end_date_complete = rds_availability + '-' + time_addon()

    # list all tags (in Key: Value format) and put them in a dictionary
    tag_response = rds_cli.list_tags_for_resource(
        ResourceName = rds_arn,
    )
    # V Tests below V
    print ('Value number 1:')
    print (rds_arn)
    print ('Window time:')
    print (rds_availability)
    print ('Complete end window time:')
    print (window_end_date_complete)
    # print ('Tag dictionary')
    # print (tag_response)
    # /\ Tests above /\