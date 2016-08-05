# README #

pyControl is a project to develop software and hardware for controlling behavioural experiments based around the [Micropython](http://www.micropython.org/) microcontroller.

For more information please see the [Wiki](https://bitbucket.org/takam/pycontrol/wiki/Home)

## How to configure the project

1. Copy the folder pycontrol\example_config to pycontrol\config and change it according your needs.

2. Copy the file pycontrol\settings.py to user_settings.py and place it in the top level folder. You should not change pycontrol\settings.py directly since this file is shared by all users.

3. Create 'tasks' dir on the path you defined under pycontrol\config\config.py and put your tasks files inside it.

4. Create 'data' dir on the path you defined under pycontrol\config\config.py.

Typical structure for a well configured project:

	| example_tasks # DO NOT CHANGE
	| data # output from running task
	| tasks # place your tasks here
	| user_settings.py # adjust your settings here (overrides settings.py)
	| framework 
		| pyControl # framework code to be uploaded
	| pycontrol # source code
		| board
		| example_config # DO NOT CHANGE
		| config # adjust your project configuration here
		| entities
		settings.py # DO NOT CHANGE
	| schematics
	| tests

Note: other unrelevant files are omitted here.


## Run project

On the top level folder invoke the following command:

	python3 -m pycontrol