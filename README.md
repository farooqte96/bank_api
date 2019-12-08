# bank_api
A bank REST API to register the user and perform required transactions

### Project Build & Installation:

1. Clone the project and browse to repo containing docker-compose.yml file
2. Install docker-compose on your system because we are going to deploy this service locally inside containers.
3. To build the services, run "docker-compose build"
4. When build is complete, then run the command "docker-compose up" to start the built services.

### REST API Endpoints:
bank_api service starts on port 5000 and is connected to mongodb server running on port 27017. Following api end points exist in bank_api service:

1. /register : This api-end point is a POST Request which requires username and password in json-format to register the user. We also need to create a user with name "BANK" which would be used as useraccount of bank itself.

2. /add: To add some amount into a user-account, this requires username, password and amount that would be added to user-account.
3. /transfer: To transfer some amount to another account, user needs to provide username, password, amount to transfer and beneficiary username.

3. /takeloan: this api-end point takes username, password and amount to take as loan.
4. /payloan: This api-end point takes username, password and amount to pay back to "BANK".
