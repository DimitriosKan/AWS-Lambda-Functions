# AWS-Lambda-Functions
A repository of lambda functions to trigger, manage, monitor all those pesky AWS Services

_Note: Dive into the code to understand more_

### Three scripts to rule all RDS instances:
__start_instance.py__ will check for certain tags and run the instances which evaluate True  
__stop_instance.py__ will check more tags and stop the instances that evaluate True (or None)  
__status_check_instance.py__ is a support script which at this stage is optimal for manual running.  
After you are starting on stopping any of your instances, run this to see the true state of it as it goes.  
Goal for this is to have it return or set a thing to automate another thingz
