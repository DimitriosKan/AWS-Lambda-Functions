# Function to start the instances which fulfill below requirements:
#  - State = Down
#  - patch window weekday = today's weekday
#  - patch window start date > today's date
# Should be executed / triggered with an event about an hour or half an hour before patch window

import boto3
import datetime
import time

rds_cli = boto3.client('rds')
rds_response = rds_cli.describe_db_instances()
available_rds = {}
parsed_times = {}
a_form = '%a:%H:%M- %d %m %Y'

# get current time in format day:hr:sec (lower case in 'day' is also improtant)
def current_time(form):
    current_time = datetime.datetime.now().strftime(form)
    return current_time

# snip the end bits to get a check date, which will match the current one
def time_addon():
    time_addon = datetime.datetime.now().strftime(a_form).split('-')
    return time_addon[1]

# parse the data and chenge up it's container (make it in comparable format)
def time_parse(cur_time, form):
    tag_time = datetime.datetime.strptime(cur_time, form)
    return tag_time

# get the string of any date I'm evaluating
# split it by ':'
# and get the first value (week day)
def week_day(date_str):
    week_day = date_str.split(':')
    return week_day[0]

# populate dict with available instances
for i in rds_response['DBInstances']:
    # this dict has the instance name (key), instance arn ([0] list value), maintenance window {start} ([1] list value)
    available_rds[i['DBInstanceIdentifier']] = [i['DBInstanceArn'], str(i['PreferredMaintenanceWindow'].split('-')[0]).capitalize()]


for key in available_rds:
    print ()
    print (f'Working {key} ...')
    # get the arn from the dict by key name
    rds_arn = available_rds.get(key, 'Not Found !')[0]
    rds_availability = available_rds.get(key, 'Not Found !')[1]
    
    # put it in comparable format
    window_start_date_complete = rds_availability + '-' + time_addon()
    # add the parsed values to a dictionary (window value - current value)
    parsed_times[time_parse(window_start_date_complete, a_form)] = time_parse(current_time(a_form), a_form)

    # list all tags (in Key: Value format) and put them in a dictionary
    tag_response = rds_cli.list_tags_for_resource(
        ResourceName = rds_arn,
    )
    try:
        state_pass = None
        outside_window = None
        for key_val in tag_response['TagList']:
            # check through all the tags in dictionary
            # print the dictionary (key_val) which will be used later
            print (key_val)

            # Do the checks on those Keys:
            if key_val['Key'] == 'State':
                if key_val['Value'] == 'Up':
                    state_pass = True
                # check if the service is Down (or equivalent)
                elif key_val['Value'] == 'Down':
                    state_pass = False
                    # evaluate if todays week day matches the widow start one
                    if week_day(rds_availability) == week_day(current_time(a_form)):
                        print (f'{week_day(rds_availability)} - {week_day(current_time(a_form))}')
                        print ('The week day match check: Fulfilled')
                        # check if the key (window start date) is lower or higher than current date
                        for i in parsed_times:
                            if i < parsed_times.get(i, 'Not Found !'):
                                print (f"{i} < {parsed_times.get(i, 'Not Found !')}")
                                print ('Current time evaluated as HIGHER')
                                outside_window = False
                            elif i > parsed_times.get(i, 'Not Found !'):
                                print (f"{i} > {parsed_times.get(i, 'Not Found !')}")
                                print ('Current time evaluated as LOWER')
                                outside_window = True
                            else:
                                print ('date.time Comparison failed')
                            print (f'Window bounds evaluated to: {outside_window}')
                    elif week_day(rds_availability) != week_day(current_time(a_form)):
                        print (f'{week_day(rds_availability)} - {week_day(current_time(a_form))}')
                        print ('The week day match check: Failed')
                        outside_window = False
                print (f'State value evaluated to: {state_pass}')

        # if the state tag evaluated to False (aka Down)
        if state_pass == False and outside_window == True:
            print ('STARTING ...')
            # V Start instance V
            rds_cli.start_db_instance(
                DBInstanceIdentifier=key
            )
            print (f'{key} was started !')
            # V Change State tag to Up V
            rds_cli.add_tags_to_resource(
                ResourceName=rds_arn,
                Tags=[
                    {
                        'Key': 'State',
                        'Value': 'Patch'
                    }
                ]
            )
            print (f'Instance ({key}) is Up')
        # this evaluates when the instance is Down but the check is in the patch window
        elif state_pass == False and outside_window != True:
            print ('*DOING NOTHING* because current time is in the path window')
        # if it's already Down, tell the user and do nothing else
        elif state_pass == True:
            print ('*DOING NOTHING*: State is Up')
        # if something goes wrong on value level error here
        elif state_pass == None or outside_window == None:
            print ('*DOING NOTHING*: State is None')
    # this triggers when the instance has been stopped and you run that again
    except:
        print ('The dictionary is non existent')