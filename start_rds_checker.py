import boto3
import datetime
import time

# Backlog
    # get instance tags [DONE]
    # check if state tag is down (you have that in code) [CHECK IF STABLE !]
    # if curret date tag is < than start date tag - 2 hrs (test it by getting current time, adding 2 hours to it, print, equate to two hours in the future) [CHECK WITH HIGHER VALUE]
    # spin it up (you have that in code) [CHECK ACTUALLY]
    # check in every so minutes if the DBInstanceStatus is avaliable [MAJOR ADDITION]
    # ONLY AFTER THAT maybe use a wait (test by getting current time, do a wait for 2 hours, print current time again)
    # stop it after the 2 hours (you have that in code) [ADD]

lamb_cli = boto3.client('lambda')
rds_cli = boto3.client('rds')
rds_response = rds_cli.describe_db_instances()
available_rds = {}

# check the state of instance (with specific 'key' value) - 2.0
def check_if_up(key):
    single_rds_response = rds_cli.describe_db_instances(
            DBInstanceIdentifier=key
        )
    for i in single_rds_response['DBInstances']:
        return i['DBInstanceStatus']

'''
# check the state of instance - 0.1
def check_state(key):
    single_rds_response = rds_cli.describe_db_instances(
        DBInstanceIdentifier=key
    )
    print ('Check state:')
    for i in single_rds_response['DBInstances']:
        while True:
            if i['DBInstanceStatus'] != 'available':
                print (f"{i['DBInstanceIdentifier']} - {i['DBInstanceStatus']}")

            elif i['DBInstanceStatus'] == 'available':
                print ('Instance is up')
                print ('Continuing onwards ...')
                # return i['DBInstanceStatus']
                break
            time.sleep(45)
'''

# get current date in desired format (needs to be formatted with the parser)
def current_time():
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return current_time

# parse the data and chenge up it's container (make it in comparable format)
def time_parse(key_val):
    tag_time = datetime.datetime.strptime(key_val, '%Y-%m-%d %H:%M:%S')
    return tag_time

# if start time tag (but 2 hours later) is equal or higher than current time tag
# few minutes leeway so the wait function doesn't fail (there's about a few seconds of delay)
def done_block(set_time):
    update_state = None
    # if current time is higher or equal to the new time (static set from the call of the update function) plus update time
    # set state to identify the pass of the update
    if datetime.timedelta(seconds=70) + time_parse(set_time) >= time_parse(current_time()):
        update_state = True
        # print (datetime.timedelta(seconds=70) + time_parse(set_time))
        print (f'[c]{current_time()} <= [s]{set_time} ?')
        print (f'Update Done [{update_state}]')
        return update_state
    # if current time is lower to the new time (static set from the call of the udpate function) plus update time
    # set state to identify the fail of the update
    elif datetime.timedelta(seconds=70) + time_parse(set_time) < time_parse(current_time()):
        update_state = False
        #print (datetime.timedelta(seconds=70) + time_parse(set_time))
        print (f'[c]{current_time()} >= [s]{set_time} ?')
        print (f'Update not allowed ... [{update_state}]')
        return update_state
    else:
        print ('ERROR')

# populate dict with available instances
for i in rds_response['DBInstances']:
    available_rds[i['DBInstanceIdentifier']] = i['DBInstanceArn']


for key in available_rds:
    print ()
    print (f'Working {key} ...')
    # get the arn from the dict by key name
    rds_arn = available_rds.get(key, 'Not Found !')
    
    # list all tags (in Key: Value format) and put them in a dictionary
    tag_response = rds_cli.list_tags_for_resource(
        ResourceName = rds_arn,
    )
    try:
        # * check through all the tags in dictionary *
        # print the dictionary (key_val) which will be used later
        state_pass = None
        for key_val in tag_response['TagList']:
            print (key_val)

            # Do the checks on those Keys:
            # check if the service is up (or equivalent)
            if key_val['Key'] == 'State':
                if key_val['Value'] == 'Up':
                    state_pass = True
                elif key_val['Value'] == 'Down':
                    state_pass = False
                print (f'Value evaluated to: {state_pass}')
        try:
            # if the state tag evaluated to False (aka Down)
            if state_pass == False:
                print ('STARTING ...')
                # V Start instance V
                rds_cli.start_db_instance(
                    DBInstanceIdentifier=key
                )
                print (f'{key} was started !')

                # V Check if instance is available yet V
                print (f'Checking state ({key}):')
                while True:
                    value = check_if_up(key)
                    try:
                        if value != 'available':
                            print (f'{key}: {value}')
                            time.sleep(35)
                        elif value == 'available':
                            # V Change tag to Up V
                            rds_cli.add_tags_to_resource(
                                ResourceName=rds_arn,
                                Tags=[
                                    {
                                        'Key': 'State',
                                        'Value': 'Up'
                                    }
                                ]
                            )
                            print (f'Instance ({key}) is Up')
                            break
                        else:
                            print ('Failed ...')
                            break
                    except:
                        print ('check availability failed ...')

                # set_time is the start of the update block (after the spin up above)
                set_time = current_time()

                # V Block time for update V
                time.sleep(60)

                # sleep complete
                print ('1 minutes later ... ')

                # check the update state (aka if the update has passed)
                update_state = done_block(set_time)
                try:
                    if update_state == True:
                        # V Stop instance V
                        print (f'Stopping {key} ...')
                        rds_cli.stop_db_instance(
                            DBInstanceIdentifier=key
                        )
                        print (f'{key} was stopped !')
                        # re-tag with Down tag (helps if update fails while isntance is up)
                        rds_cli.add_tags_to_resource(
                            ResourceName=rds_arn,
                            Tags=[
                                {
                                    'Key': 'State',
                                    'Value': 'Down'
                                }
                            ]
                        )
                    elif update_state == False:
                        print ('Update was not complete ...')
                    else:
                        print (update_state)
                except:
                    print ('Post update has failed ...')
            # if it's already Down, tell the user and do nothing else
            elif state_pass == True:
                print ('*DOING NOTHING*: State is Up')
            # if something goes wrong on value level error here
            elif state_pass == None:
                print ('*DOING NOTHING*: State is None')
        # if something goes wrong on key: value level error here
        except:
            print ('Something went wrong ...')

    # this triggers when the instance has been stopped and you run that again
    except:
        print ('The dictionary is non existent')