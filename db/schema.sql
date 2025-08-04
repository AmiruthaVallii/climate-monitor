DROP TABLE IF EXISTS future_weather_prediction;
DROP TABLE IF EXISTS historical_weather_readings;
DROP TABLE IF EXISTS historical_air_quality;
DROP TABLE IF EXISTS weather_readings;
DROP TABLE IF EXISTS air_quality_readings;
DROP TABLE IF EXISTS location_assignment;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS flood_area_assignment;
DROP TABLE IF EXISTS locations;
DROP TABLE IF EXISTS flood_warnings;
DROP TABLE IF EXISTS historical_floods;
DROP TABLE IF EXISTS flood_severity;
DROP TABLE IF EXISTS flood_areas;


CREATE TABLE "users"(
    "user_id" INTEGER GENERATED ALWAYS AS IDENTITY,
    "first_name" TEXT NOT NULL,
    "last_name" TEXT NOT NULL,
    "email" TEXT NOT NULL UNIQUE,
    "phone_number" TEXT NOT NULL UNIQUE,
    "username" TEXT NOT NULL UNIQUE,
    "password" TEXT NOT NULL,
    PRIMARY KEY (user_id)
);

CREATE TABLE "locations"(
    "location_id" INTEGER GENERATED ALWAYS AS IDENTITY,
    "location_name" TEXT NOT NULL UNIQUE,
    "latitude" FLOAT NOT NULL,
    "longitude" FLOAT NOT NULL,
    PRIMARY KEY (location_id)
);

CREATE TABLE "location_assignment"(
    "location_assignment_id" INTEGER GENERATED ALWAYS AS IDENTITY,
    "user_id" INTEGER NOT NULL,
    "location_id" INTEGER NOT NULL,
    "subscribe_to_alerts" BOOLEAN NOT NULL,
    "subscribe_to_summary" BOOLEAN NOT NULL,
    PRIMARY KEY (location_assignment_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (location_id) REFERENCES locations(location_id)
);
CREATE TABLE "flood_areas"(
    "flood_area_id" INTEGER GENERATED ALWAYS AS IDENTITY,
    "flood_area_code" TEXT NOT NULL UNIQUE,
    PRIMARY KEY (flood_area_id)
);
CREATE TABLE "flood_area_assignment"(
    "flood_area_assignment_id" INTEGER GENERATED ALWAYS AS IDENTITY,
    "location_id" INTEGER NOT NULL,
    "flood_area_id" INTEGER NOT NULL,
    PRIMARY KEY (flood_area_assignment_id),
    FOREIGN KEY (location_id) REFERENCES locations(location_id),
    FOREIGN KEY (flood_area_id) REFERENCES flood_areas(flood_area_id)
);


CREATE TABLE "weather_readings"(
    "weather_reading_id" INTEGER GENERATED ALWAYS AS IDENTITY,
    "timestamp" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "location_id" INTEGER NOT NULL,
    "rainfall_last_15_mins" FLOAT NOT NULL,
    "snowfall_last_15_mins" FLOAT NOT NULL,
    "current_temperature" FLOAT NOT NULL,
    "wind_speed" FLOAT NOT NULL,
    "wind_gust_speed" FLOAT NOT NULL,
    "wind_direction" SMALLINT NOT NULL,
    PRIMARY KEY (weather_reading_id),
    FOREIGN KEY (location_id) REFERENCES locations(location_id)
);
CREATE TABLE "air_quality_readings"(
    "air_quality_reading_id" INTEGER GENERATED ALWAYS AS IDENTITY,
    "timestamp" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "location_id" INTEGER NOT NULL,
    "air_quality_index" SMALLINT NOT NULL,
    "carbon_monoxide" FLOAT NOT NULL,
    "nitrogen_monoxide" FLOAT NOT NULL,
    "ammonia" FLOAT NOT NULL,
    "nitrogen_dioxide" FLOAT NOT NULL,
    "ozone" FLOAT NOT NULL,
    "sulphur_dioxide" FLOAT NOT NULL,
    "pm2_5" FLOAT NOT NULL,
    "pm10" FLOAT NOT NULL,
    PRIMARY KEY (air_quality_reading_id),
    FOREIGN KEY (location_id) REFERENCES locations(location_id)
);
CREATE TABLE "flood_severity"(
    "severity_id" INTEGER NOT NULL GENERATED ALWAYS AS IDENTITY,
    "severity_level" INTEGER NOT NULL UNIQUE,
    "severity_name" TEXT NOT NULL UNIQUE,
    "severity_meaning" TEXT NOT NULL,
    PRIMARY KEY (severity_id)
);
CREATE TABLE "flood_warnings"(
    "flood_warnings_id" INTEGER GENERATED ALWAYS AS IDENTITY,
    "flood_area_id" INTEGER NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "timestamp" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "severity_id" INTEGER NOT NULL,
    "location_description" TEXT,
    "message" TEXT,
    "notifications_sent" BOOLEAN NOT NULL,
    PRIMARY KEY (flood_warnings_id),
    FOREIGN KEY (flood_area_id) REFERENCES flood_areas(flood_area_id),
    FOREIGN KEY (severity_id) REFERENCES flood_severity(severity_id)
);


CREATE TABLE "historical_weather_readings"(
    "historical_reading_id" INTEGER GENERATED ALWAYS AS IDENTITY,
    "timestamp" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "location_id" INTEGER NOT NULL,
    "hourly_rainfall" FLOAT,
    "hourly_snowfall" FLOAT,
    "hourly_temperature" FLOAT,
    "hourly_wind_speed" FLOAT,
    "hourly_wind_gust_speed" FLOAT,
    "hourly_wind_direction" SMALLINT,
    PRIMARY KEY (historical_reading_id),
    FOREIGN KEY (location_id) REFERENCES locations(location_id)

);
CREATE TABLE "historical_air_quality"(
    "historical_air_quality_id" INTEGER GENERATED ALWAYS AS IDENTITY,
    "timestamp" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "location_id" INTEGER NOT NULL,
    "hourly_air_quality_index" SMALLINT,
    "hourly_carbon_monoxide" FLOAT,
    "hourly_nitrogen_dioxide" FLOAT,
    "hourly_nitrogen_monoxide" FLOAT,
    "hourly_ammonia" FLOAT,
    "hourly_ozone" FLOAT,
    "hourly_sulphur_dioxide" FLOAT,
    "hourly_pm2_5" FLOAT,
    "hourly_pm10" FLOAT,
    PRIMARY KEY (historical_air_quality_id),
    FOREIGN KEY (location_id) REFERENCES locations(location_id)
);

CREATE TABLE "historical_floods"(
    "historical_flood_id" INTEGER GENERATED ALWAYS AS IDENTITY,
    "date" TIMESTAMP NOT NULL,
    "flood_area_id" INTEGER NOT NULL,
    "severity_id" SMALLINT NOT NULL,
    PRIMARY KEY (historical_flood_id),
    FOREIGN KEY (flood_area_id) REFERENCES flood_areas(flood_area_id),
    FOREIGN KEY (severity_id) REFERENCES flood_severity(severity_id)
);


CREATE TABLE "future_weather_prediction"(
    "prediction_id" INTEGER GENERATED ALWAYS AS IDENTITY,
    "date" DATE NOT NULL,
    "location_id" INTEGER NOT NULL,
    "mean_temperature" FLOAT,
    "max_temperature" FLOAT,
    "min_temperature" FLOAT,
    "total_rainfall" FLOAT,
    "total_snowfall" FLOAT,
    "mean_wind_speed" FLOAT,
    "max_wind_speed" FLOAT,
    PRIMARY KEY (prediction_id),
    FOREIGN KEY (location_id) REFERENCES locations(location_id)
);
