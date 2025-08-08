# Climate Monitor

Eco Intel is a centralised dashboard that unifies weather, air quality and flood data (current, past, future). It also provides a notification system to alert users of flood and weather warnings.

<div align="center">
  <img src="documentation/eco-intel-logo.png" alt="logo" width="200">
</div>

## Description

The Streamlit dashboard utilises data from a Postgres RDS, to display graphs and metrics on weather (temperature, rainfall and wind), air quality and floods. It combines real time, historical and future predictions data to compare how weather has changed and will change. It does this at a local level, allowing users to select specific cities to view how the climate is changing in that location.

The RDS schema is in 3NF, and the lambda is supplied with data from a variety of ETLs runs on Lambda functions which collect data from an array of endpoints.

## Getting Started

### Prerequisites
Install docker locally
Install PostgreSQL command-line client (psql)
Install Python 3.13.5

### Installing

Inside the terraform folder, main.tf provides all the resources to host our pipelines, RDS and dashboard.

Once these resources are provisioned we can configure our RDS. Connect to the RDS using the password you set in variables.tf, and the dbname and username defined in the RDS definition in main.tf, and finally the host address which will be found on the AWS console. Then enter the db directory and enter these variables into a .env file. Create a venv and install requirements.txt.

Next run:
```
psql -h [host address] -U [username] -d [dbname] -p 5432 -f schema.sql
psql -h [host address] -U [username] -d [dbname] -p 5432 -f seed.sql
```

Which will set up the schema and seed the database with flood severities and initial locations.

To seed all the flood areas in the country run:
```
python3 seed_flood_areas.py
```

To upload historical flood data for the country run:
```
python3 upload_historic_floods.py
```

To get historic, future weather and air quality data for the seeded locations and also assign them flood areas,
change the directory into the db/insert-new-location folder (and install requirements) and run:
```
python3 main.py
```

The database is now set up with seed data. We now need to dockerise our lambda scripts and push them to their associated ECR repository.

The format for this always follows:
```
docker build --platform linux/amd64 --provenance=false -t [image name] .
docker tag [image name] [ecr repo url]
docker push [ecr repo url]
```

Now ensure the lambda functions are using their associated ecr image.

The dashboard should now be dockerised and pushed to it's ECR repository in the same manner.
Check that you can access it on it's URL.

The pipelines, database and dashboard are now operational.

### Documentation

#### ERD

The `erd.png` shows the schema layout for the database which is in 3NF and is followed in the schema.sql file.
![erd](<documentation/erd.png> "erd")

#### System Architecture

The `architecture-diagram.png` displays the architecture for our system. It includes an RDS which ingests data
from numerous API's via an array of Lambdas, some of which are run on eventbridge schedules. There is also
an eventbridge schedule which runs a lambda which triggers an SES service. The dashboard is hosted on AWS Fargate service.
![architecture diagram](<documentation/architecture-diagram.png> "architecture diagram")

### Scripts

#### `db/schema.sql`
A file to create the schema for the database

#### `db/seed.sql`
A file to seed the database with initial flood severity and locations.

#### `db/seed_flood_areas.py`
A file which makes a get request to a government API that lists all the English designated flood area codes.
We collect all of them and insert them into our `flood_areas` table in our database.

#### `db/seed_flood_area_assignment.py`
A file which loads all locations from the RDS and then makes a get request to a government API which returns the flood area codes for a given location (lat,lon). It finds the flood `area_codes` for every location and then matches these with `flood_area_code_ids`. It then inserts these assignments into the `flood_area_assignment` table.

####  `db/location_assignment_handler.py`
A handler function which assign flood areas based on a given location, using numerous functions from `seed_flood_area_assignment.py`

#### `db/insert-location-data/main.py`
A file which invokes the new-location-orchestrator lambda. This lambda assigns flood areas, gets historical and future data for weather and historical air quality data for a new location. This file is used to get this data for the initial seeded location and is only used on set up.

#### `extract-future/extract_future.py`
A file which creates a lambda handler which performs a get request for future climate predictions, from a given location, to an OpenMeteo api. It then inserts this data into the databases's `future_weather_predictions` table.

#### `extract-past/air_quality/extract_air_quality.py`
A file which creates a lambda handler which performs a get request for past air quality, from a given location, to an OpenWeather api. It then inserts this data into the databases's `historical_air_quality` table.

#### `extract-past/weather/extract.py`
A file which creates a lambda handler which performs a get request for historical climate data, from a given location, to an OpenMeteo api. It then inserts this data into the databases's `historical_weather_readings` table.

#### `extract-present/extract.py`
A file which creates a lambda handler which performs a get request for current weather data, for a given location, to an OpenMeteo api. It then inserts this data into the databases's `weather_readings` table.

#### `extract-present/orchestrator/orchestrator_lambda.py`
A file which creates a lambda handler which invokes the current air quality and current weather data lambda functions for every location present in the rds. This lambda is the core part of the ETL which ensures the dashboard has the latest climate and air quality data.

#### `extract-present-air-quality/extract.py`
A file which creates a lambda handler which performs a get request for current air quality data, for a given location, to an OpenWeather api. It then inserts this data into the databases's `air_quality_readings` table.

#### `live-flood-monitoring-etl/fetch_live_flood_warnings.py`
A file which creates a lambda handler which performs a get request for current live flood warnings for the entire a Gov.uk api. It ensures the flood warning is not in the database (i.e only fetches changes in warning/severity level). It combines the data with our severity_id's and flood_area_id's. It then inserts this data into the databases's `flood_warnings` table.

#### `load-historic-flood-data/upload_historic_floods.py`
Reads the historical_flood_warnings.ods and transforms it into a dataframe. It cleans the data and combines it with our corresponding flood_area_id's and severity_level_id's. It then inserts this into the `historical_floods` table of our RDS.

#### `orchestrator-new-location/new_location_orchestrator.py`
A lambda handler which invokes the historic_weather lambda, historic_air_quality lambda, the future_predictions lambda and the flood_assignment lambda. This lambda is run whenever a new location is added, to ensure static data is loaded into the RDS for it.

#### `dashboard/homepage.py`
A python script to run the streamlit homepage which contains information about the dashboard.

#### `dashboard/modules/nav.py`
A python script which creates the streamlit navigation sidebar which is used throughout the pages.

#### `dashboard/pages/weather.py`
A python script which loads historical readings, current readings and future readings to display a streamlit page with graphs and metrics of the weather a specific location over time.

#### `dashboard/pages/air_quality.py`
A python script which loads historical and current air quality to create a streamlit page of graphs and metrics of pollutant levels over time for a location.

#### `dashboard/pages/floods.py`
A python script which loads historical and current flood data to create a streamlit page of graphs and metrics of flood warnings over time for a location.

#### `dashboard/pages/login.py`
A python script which creates a streamlit login page to allow users to login or register to an account for notifications and reports.

#### `dashboard/pages/profile.py`
A python script which creates a streamlit page that can only be accessed after login. It allows users to add new locations to be tracked by the dashboard and change notification preferences.

#### `notifications/notification.py`
A python script that defines an AWS Lambda function that monitors recent weather, flood, and air quality data stored in an RDS database, detects conditions exceeding predefined safety thresholds, and sends targeted alert emails to subscribed users via Amazon SES. It retrieves unsent flood warnings, recent weather and AQI readings, evaluates them against risk thresholds, and formats alerts into styled HTML emails for immediate distribution.

#### `daily-summary/summary.py`
A python script that defines an AWS Lambda function that retrieves the past 24 hour weather and air quality data from the RDS database, formats it into text and HTML reports, and sends daily summary emails to subscribed users via Amazon SES.
