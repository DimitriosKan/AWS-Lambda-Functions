import boto3
import datetime

# one drawback here is that the weekday theoretically doesn#t matter
# in that case this function will have to run Only for the day of the window

rds_cli = boto3.client('rds')
rds_response = rds_cli.describe_db_instances()
form = '%a:%H:%M- %d %m %Y'

# get current time in format day:hr:sec (lower case in 'day' is also improtant)
def current_time():
    current_time = datetime.datetime.now().strftime(form)
    return current_time

# here I just snip the end bits to get a check date, which will match the current one
def time_addon():
    time_addon = datetime.datetime.now().strftime(form).split('-')
    # print (time_addon[1])
    return time_addon[1]

# parse the data and chenge up it's container (make it in comparable format)
def time_parse(cur_time):
    tag_time = datetime.datetime.strptime(cur_time, form)
    return tag_time

# get the string of any date I'm evaluating
# split it by ':'
# and get the first value (week day)
def week_day(date_str):
    week_day = date_str.split(':')
    return week_day[0]

dicshon = {}

# gets date in format:
# sat:04:53-sat:05:23
for i in rds_response['DBInstances']:
    window_time = i['PreferredMaintenanceWindow'].split('-')
    # print (window_time)
    # available_rds[i['DBInstanceIdentifier']] = i['DBInstanceArn']
    # this print's only the end Day:hr:sec of the range (capital in 'Day' is important)
    window_end = str(window_time[1]).capitalize()
    window_start = str(window_time[0]).capitalize()
    window_end_date_complete = window_end + '-' + time_addon()
    window_start_date_complete = window_start + '-' + time_addon()
    print ()
    print (f'* {window_end} *')
    print (type(window_end))

    # Note: I don't check the date of the month here. I check if the week day matches,
    # which means the date will as well, considering this is a weekly update
    # addressing the weekday match issue highlighted
    # here I call the week_day function (go to week_day function above)
    if week_day(window_end) == week_day(current_time()):
        print (f'{week_day(window_end)} - {week_day(current_time())}')
        print ('The week day match check: Fulfilled')

    elif week_day(window_end) != week_day(current_time()):
        print (f'{week_day(window_end)} - {week_day(current_time())}')
        print ('Week day match check: Failed !')
    else:
        print (f'{week_day(window_end)} - {week_day(current_time())}')
        print ('Something went wrong there ...')

    '''
    Test Prints start
    '''
    ## add extra values to the string of window_time
    # pull everything after %M and paste it at end of other thing
    print ()
    print ('Time addon')
    print (time_addon())
    print (type(time_addon()))
    # get the time_addon (the value fetched from the window)
    # and add the addon to it (which makes it work for the day of check)
    print ()
    print ('Time added on')
    #format it so it works with the other things
    print (window_end_date_complete)
    print (type(window_end_date_complete))
    print ()
    print ('Current time - raw')
    print (current_time())
    print (type(current_time()))
    print ()
    print ('Current time - parsed')
    print (time_parse(current_time()))
    print (type(time_parse(current_time())))
    print ()
    print ('Window time - parsed')
    print (time_parse(window_end_date_complete))
    print (type(time_parse(window_end_date_complete)))
    '''
    Test Prints over
    '''

    # add the parsed values to a dictionary (window value - current value)
    dicshon[time_parse(window_end_date_complete)] = time_parse(current_time())

print ()
print (dicshon)
print ()

# go through dictionary checking values
# format: window_end - current_time
for i in dicshon:
    if i < dicshon.get(i, 'Not Found !'):
        print (f"{i} < {dicshon.get(i, 'Not Found !')}")
        print ('Current time evaluated as HIGHER')
    elif i > dicshon.get(i, 'Not Found !'):
        print (f"{i} > {dicshon.get(i, 'Not Found !')}")
        print ('Current time evaluated as LOWER')
    else:
        print ('Oopsie')