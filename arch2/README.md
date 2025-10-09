# Architecture 2 - Microservices Architecture

## To get it working:
as of October 2nd, 2025


### 1. run the client server and enter in via bash
`docker-compose run client /bin/bash`

### 2. run the cli.py and run these commands
- `python cli.py signup username password`
- `python cli.py login username password`
- `python cli.py upload somefile.txt`
- `python cli.py download somefile.txt`
- `python cli.py delete somefile.txt`
- `python cli.py list`

some responses you should see
- signup: `{'message': 'Signup successful!'}`
- login:  `Login successful!`
- upload: `{'path': '/storage/somefile.txt', 'status': 'saved'}`
- download: `Downloaded to somefile.txt`
- delete: `Deletion successful` 
- list: `[{'filename': 'somefile.txt', 'password': '', 'path': '/storage/somefile.txt', 'size': 6, 'user': None, 'version': 1}]` or `[]`

### (optional) 3. open another terminal and enter the storage container
`docker exec -it arch1-storage-1 sh `

list the storage folder `ls /storage`

and you should see the `somefile.txt` there. 


### some assumptions
- no real error handling were made when creating this project. we just hope everything worked as intented lol. 
- current it is: (i updated it in the storage and metadata code already)
    - service - 5000
    - metadata - 5001
    - storage - 5002