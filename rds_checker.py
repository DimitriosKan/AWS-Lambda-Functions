import boto3
from datetime import datetime

client = boto3.client('rds')

response = client.describe_db_instances()

# here you can define what instances are going to be considered
# eg. ... = 'db-one', 'db-two'
set_list = 'database-1', 'database-2'

available_rds = {}

# get the name: arn key: val pair of available RDS DBs
for i in response['DBInstances']:
    available_rds[i['DBInstanceIdentifier']] = i['DBInstanceArn']

# fetch the key of all avaialble instances
for key in available_rds:
    # check if the key matches the set_list
    if key in set_list:
        print (f'Working {key} ...')
        rds_arn = available_rds.get(key, 'Not Found !')
        
        # list all tags (in Key: Value format) and put them in a dictionary
        tag_response = client.list_tags_for_resource(
            ResourceName = rds_arn,
        )

        # get current time
        current_time = datetime.now()

        # convert string to datetime
        def time_eval(key_val):
            tag_time = datetime.strptime(key_val, '%Y-%m-%d %H:%M:%S')

            return tag_time

        # check through all the tags in dictionary
        # print the dictionary (key_val) which will be used later
        for key_val in tag_response['TagList']:
            print (key_val)
            
            try:
                # if the dictionary contains (Key strings of tags to check for)
                if key_val['Key'] in ('State', 'Created'):
                    # Do the checks on those Keys:
                    # check if the service is up (or equivalent)
                    if key_val['Value'] == 'Up':
                        print ('Value is a: pass')
                    
                    # get current time and evaluate if it's older than ['Value']
                    elif time_eval(key_val['Value']) < current_time:
                        print (f"Tag date:{time_eval(key_val['Value'])} - Current date:{current_time}")
                        # print (f"Tag date:{time_eval(key_val['Value'])}{type(time_eval(key_val['Value']))} - Current date:{current_time}{type(current_time)}")
                        print ('Value is a: pass')
                    
                    # else throw exception or notify the user that the Value was not evaluated
                    else:
                        print ('Value is a: fail')
                else:
                    print ('Key does not match with check')
            except:
                print ('The dictionary is non existent')