# Function to stop the instances which fulfill below requirements:
# Case 1: Daily instance check (take down instances that are up but not used)
#  - State = Up
#  - Values of key Started < today's date evaluates to True
#  - Values of key Started > today's date evaluates to False
#  - Values of key Stopped > today's date evaluates to True
#  - Values of key Stopped < today's date evaluates to False
#  - If Started or Stopped are False, stop instance (means that we are outside the assigned bounds)
#  - If Started and Stopped are True, do nothing (means that we are instide the assigned bounds)
#  - If any of the alue are None do nothing and notify the user
# ** Should be executed / triggered with an event whenever you want your instances to be checked for Up status
# Case 2: Weekly or Monthly instance take down after completion of patch
# Here it checks with both start and end patch window values
#  - State = Patch
#  - patch window weekday = today's weekday
#  - today's date < patch window start date evaluates to True
#  - patch window end date < today's date evaluates to True
#  - start date < current date and end date is > current date evaluates to False
#  - If outside window = True, stop instance (because current time is outside patch window)
#  - If outside window = False, do nothing (because it's in patch window *maybe something failed)
#  - Else Stop instance and tell user it's due to None value
# ** Should be executed / triggered with an event few minutes after patch window End time

import boto3
import datetime

rds_cli = boto3.client('rds')
rds_response = rds_cli.describe_db_instances()
available_rds = {}
a_form = '%a:%H:%M- %d %m %Y'
b_form = '%Y-%m-%d %H:%M:%S'

# get current time in format day:hr:sec (lower case in 'day' is also improtant)
def current_time(form):
    current_time = datetime.datetime.now().strftime(form)
    return current_time

# snip the end bits to get a check date, which will match the current one
def time_addon():
    time_addon = datetime.datetime.now().strftime(a_form).split('-')
    # print (time_addon[1])
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

# function to run stop commands, used multiple times
def stop_instance(key, rds_arn):
    print ('**STOPPING**')
    stop_resp = rds_cli.stop_db_instance(
        DBInstanceIdentifier=key
    )
    print (f'{key} was stopped !')
    rds_cli.add_tags_to_resource(
        ResourceName=rds_arn,
        Tags=[
            {
                'Key': 'State',
                'Value': 'Down'
            }
        ]
    )
    print ('State set to Down !')

# get the name: arn key: val pair of available RDS DBs
for i in rds_response['DBInstances']:
    # this dict has the instance name (key), instance arn ([0] list value), maintenance window start ([1] list value), maintenance window stop ([2] list value)
    available_rds[i['DBInstanceIdentifier']] = [i['DBInstanceArn'], str(i['PreferredMaintenanceWindow'].split('-')[0]).capitalize(),str(i['PreferredMaintenanceWindow'].split('-')[1]).capitalize()]

# fetch the key of all available instances
for key in available_rds:
    print ()
    print (f'Working {key} ...')
    # dictionary of values for each instance and it's comparable times
    updated_parsed_times = {}
    rds_arn = available_rds.get(key, 'Not Found !')[0]
    bottom_window = available_rds.get(key, 'Not Found !')[1]
    rds_availability = available_rds.get(key, 'Not Found !')[2]

    # formatting strings for comaprison with current date
    window_start_date_complete = bottom_window + '-' + time_addon()
    window_end_date_complete = rds_availability + '-' + time_addon()
    # add the parsed values to a dictionary (window start value - window end value)
    updated_parsed_times[time_parse(window_start_date_complete, a_form)] = time_parse(window_end_date_complete, a_form)

    # list all tags (in Key: Value format) and put them in a dictionary
    tag_response = rds_cli.list_tags_for_resource(
        ResourceName = rds_arn,
    )

    # set default states helping with error handling
    state_pass = None
    outside_window = None
    stop_pass = None
    start_pass = None
    # check through all the tags in dictionary
    # print the dictionary (key_val) which will be used later
    for key_val in tag_response['TagList']:
        print (key_val)
        # Do the checks on those Keys:
        # check if the service is up (or equivalent)
        if key_val['Key'] == 'State':
            if key_val['Value'] == 'Up':
                state_pass = True
                if key_val['Key'] == 'Started':
                    if time_parse(key_val['Value'], b_form) < time_parse (current_time(b_form), b_form):
                        print (f"Tag date:{time_parse(key_val['Value'], b_form)} < Current date:{time_parse (current_time(b_form), b_form)}")
                        start_pass = True
                    elif time_parse(key_val['Value'], b_form) > time_parse (current_time(b_form), b_form):
                        print (f"Tag date:{time_parse(key_val['Value'], b_form)} > Current date:{time_parse (current_time(b_form), b_form)}")
                        start_pass = False
                    print (f'Value evaluated to: {start_pass}')

                if key_val['Key'] == 'Stopped':
                    if time_parse(key_val['Value'], b_form) > time_parse (current_time(b_form), b_form):
                        print (f"Tag date:{time_parse(key_val['Value'], b_form)} > Current date:{time_parse (current_time(b_form), b_form)}")
                        stop_pass = True
                    elif time_parse(key_val['Value'], b_form) < time_parse (current_time(b_form), b_form):
                        print (f"Tag date:{time_parse(key_val['Value'], b_form)} < Current date:{time_parse (current_time(b_form), b_form)}")
                        stop_pass = False
                    print (f'Value evaluated to: {stop_pass}')

            elif key_val['Value'] == 'Patch':
                # evaluate if todays week day matches the widow start one
                if week_day(rds_availability) == week_day(current_time(a_form)):
                    print (f'{week_day(rds_availability)} - {week_day(current_time(a_form))}')
                    print ('The week day match check: Fulfilled')
                    # check if the key (window start date) is lower or higher than current date
                    for i in updated_parsed_times:
                        if i > time_parse(current_time(a_form), a_form):
                            print (f"{time_parse(current_time(a_form), a_form)} < {i} - {updated_parsed_times.get(i, 'Not Found !')}") 
                            print ('Current time is outside the window range')
                            outside_window = True
                        elif updated_parsed_times.get(i, 'Not Found !') < time_parse(current_time(a_form), a_form):
                            print (f"{i} - {updated_parsed_times.get(i, 'Not Found !')} > {time_parse(current_time(a_form), a_form)}")
                            print ('Current time is outside the window range')
                            outside_window = True
                        elif i < time_parse(current_time(a_form), a_form) and updated_parsed_times.get(i, 'Not Found !') > time_parse(current_time(a_form), a_form):
                            print (f"{i} - {time_parse(current_time(a_form), a_form)} - {updated_parsed_times.get(i, 'Not Found !')}")
                            print ('Current time is in the window range')
                            outside_window = False
                        else:
                            print ('Oopsie ... Evaluating the current to window time comparison failed')
                    print (f'Window bounds evaluated to: {outside_window}')
                elif week_day(rds_availability) != week_day(current_time(a_form)):
                    print (f'{week_day(rds_availability)} - {week_day(current_time(a_form))}')
                    print ('Week day match check: Failed !')
                else:
                    print (f'{week_day(rds_availability)} - {week_day(current_time(a_form))}')
                    print ('Something went wrong there ...')

            elif key_val['Value'] == 'Down':
                state_pass = False
            print (f'State value evaluated to: {state_pass}')

    # if the state tag evaluated to True (aka Up)
    # This will be the one called if checking for Up instances once a day
    if state_pass == True:
        if start_pass == False or stop_pass == False:
            stop_instance(key, rds_arn)
        elif start_pass == True and stop_pass == True:
            print ('*DOING NOTHING* because current date is in range')
        elif start_pass == None or stop_pass == None:
            print ('*DOING NOTHING* because either of the range values is undefined')
    # if it's already Down, tell the user and do nothing else
    elif state_pass == False:
        print ('*DOING NOTHING* because State is Down')
    # if state tag Evaluates to None (aka Patch or Else)
    # This will be the one called if checking for Patch instances once a week/month
    elif state_pass == None:
        if outside_window == True:
            stop_instance(key, rds_arn)
        elif outside_window == False:
            print ('*DOING NOTHING* because current time is still in patch window')
        else:
            stop_instance(key, rds_arn)
            print ('*STOPPING* because State is None')