import boto3
from datetime import datetime

def lambda_handler(event, context):
    lamb_cli = boto3.client('lambda')
    rds_cli = boto3.client('rds')
    print ('Checking environment variables ...')
    rds_response = rds_cli.describe_db_instances()
    available_rds = {}

    # run the check for the lambda env variables
    lamb_response = lamb_cli.get_function_configuration(
        FunctionName='test_func'
    )
    DBFunction = lamb_response['Environment']['Variables']['DBClusterFunction']
    print (f'RDS service requested for DB CLuster START/STOP: {DBFunction}')

    # check the status of the env function (DBFunction) is equal to ...
    if DBFunction == 'STOP':
        # get the name: arn key: val pair of available RDS DBs
        for i in rds_response['DBInstances']:
            available_rds[i['DBInstanceIdentifier']] = i['DBInstanceArn']

        # fetch the key of all avaialble instances
        for key in available_rds:
            print ()
            print (f'Working {key} ...')
            rds_arn = available_rds.get(key, 'Not Found !')
            
            # list all tags (in Key: Value format) and put them in a dictionary
            tag_response = rds_cli.list_tags_for_resource(
                ResourceName = rds_arn,
            )

            # get current time
            current_time = datetime.now()

            # convert string to datetime
            def time_eval(key_val):
                tag_time = datetime.strptime(key_val, '%Y-%m-%d %H:%M:%S')
                return tag_time

            try:
                # * check through all the tags in dictionary *
                # print the dictionary (key_val) which will be used later
                state_pass = None
                for key_val in tag_response['TagList']:
                    print (key_val)

                    # Do the checks on those Keys:
                    # check if the service is up (or equivalent)
                    # [*Edit this acording to your tag's value*]
                    if key_val['Key'] == 'State':
                        if key_val['Value'] == 'Up':
                            state_pass = True
                        elif key_val['Value'] == 'Down':
                            state_pass = False
                        print (f'Value evaluated to: {state_pass}')

                    if key_val['Key'] == 'Started':
                        if time_eval(key_val['Value']) < current_time:
                            print (f"Tag date:{time_eval(key_val['Value'])} < Current date:{current_time}")
                            # print (f"Tag date:{time_eval(key_val['Value'])}{type(time_eval(key_val['Value']))} - Current date:{current_time}{type(current_time)}")
                            start_pass = True
                        else:
                            start_pass = False
                        print (f'Value evaluated to: {start_pass}')

                    if key_val['Key'] == 'Stopped':
                        if time_eval(key_val['Value']) > current_time:
                            print (f"Tag date:{time_eval(key_val['Value'])} > Current date:{current_time}")
                            # print (f"Tag date:{time_eval(key_val['Value'])}{type(time_eval(key_val['Value']))} - Current date:{current_time}{type(current_time)}")
                            stop_pass = True
                        else:
                            stop_pass = False
                        print (f'Value evaluated to: {stop_pass}')

                try:
                    if state_pass == True:
                        if start_pass == False or stop_pass == False:
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
                        # check if the user is allwoed to have the rds up
                        elif start_pass == True and stop_pass == True:
                            print ('*DOING NOTHING* because current date is in range')
                    # if it's already Down, tell the user and do nothing else
                    elif state_pass == False:
                        print ('*DOING NOTHING* because State is Down')
                    # if something goes wrong on value level error here
                    elif state_pass == None:
                        print ('*DOING NOTHING* because State is None')
                # if something goes wrong on key: value level error here
                except:
                    print ('Something went wrong ...')

            # this triggers when the instance has been stopped and you run that again
            except:
                print ('The dictionary is non existent')

    # check the status of the env function (DBFunction) is equal to ...
    elif DBFunction == 'START':
        print ('Starting ...')