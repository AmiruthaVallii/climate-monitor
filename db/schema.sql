DROP TABLE IF EXISTS future_prediction;
DROP TABLE IF EXISTS historical_readings;
DROP TABLE IF EXISTS readings;
DROP TABLE IF EXISTS location_assignment;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS flood_area_assignment;
DROP TABLE IF EXISTS locations
DROP TABLE IF EXISTS flood_warnings;
DROP TABLE IF EXISTS historical_floods;
DROP TABLE IF EXISTS flood_severity;
DROP TABLE IF EXISTS flood_areas






CREATE TABLE users(
    "user_id" INTEGER GENERATED ALWAYS AS IDENTITY,
    "first_name" TEXT NOT NULL,
    "last_name" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "phone_number" TEXT NOT NULL,
    "username" TEXT NOT NULL,
    "password" TEXT NOT NULL,
    PRIMARY KEY (user_id)
);

CREATE TABLE "locations"(
    "location_id" INTEGER GENERATED ALWAYS AS IDENTITY,
    "location_name" TEXT NOT NULL,
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
    "flood_area_code" TEXT NOT NULL,
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


CREATE TABLE "readings"(
    "reading_id" INTEGER GENERATED ALWAYS AS IDENTITY,
    "timestamp" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "location_id" INTEGER NOT NULL,
    "rainfall_last_15_mins" FLOAT NOT NULL,
    "air_quality_index" SMALLINT NOT NULL,
    "carbon_monoxide" FLOAT NOT NULL,
    "nitrogen_dioxide" FLOAT NOT NULL,
    "ozone" FLOAT NOT NULL,
    "sulphur_dioxide" FLOAT NOT NULL,
    "pm2_5" FLOAT NOT NULL,
    "pm10" FLOAT NOT NULL,
    "current_temperature" FLOAT NOT NULL,
    "wind_speed" FLOAT NOT NULL,
    "wind_gust_speed" FLOAT NOT NULL,
    "wind_direction" SMALLINT NOT NULL,
    PRIMARY KEY (reading_id),
    FOREIGN KEY (location_id) REFERENCES locations(location_id)
);
CREATE TABLE "flood_severity"(
    "severity_id" INTEGER NOT NULL GENERATED ALWAYS AS IDENTITY,
    "severity_level" INTEGER NOT NULL,
    "severity_name" TEXT NOT NULL,
    "severity_meaning" TEXT NOT NULL,
    PRIMARY KEY (severity_id)
);
CREATE TABLE "flood_warnings"(
    "flood_warnings_id" INTEGER GENERATED ALWAYS AS IDENTITY,
    "flood_area_id" INTEGER NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "timestamp" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "severity_id" INTEGER NOT NULL,
    "description" TEXT NOT NULL,
    "notifications_sent" BOOLEAN NOT NULL,
    PRIMARY KEY (flood_warnings_id),
    FOREIGN KEY (flood_area_id) REFERENCES flood_areas(flood_area_id),
    FOREIGN KEY (severity_id) REFERENCES flood_severity(severity_id)
);


CREATE TABLE "historical_readings"(
    "historical_reading_id" INTEGER GENERATED ALWAYS AS IDENTITY,
    "date" DATE NOT NULL,
    "location_id" INTEGER NOT NULL,
    "total_rainfall" FLOAT NOT NULL,
    "mean_air_quality_index" SMALLINT NULL,
    "mean_carbon_monoxide" FLOAT NULL,
    "mean_nitrogen_dioxide" FLOAT NULL,
    "mean_ozone" FLOAT NULL,
    "mean_sulphur_dioxide" FLOAT NULL,
    "mean_pm2_5" FLOAT NULL,
    "mean_pm10" FLOAT NULL,
    "mean_temperature" FLOAT NOT NULL,
    "max_temperature" FLOAT NOT NULL,
    "min_temperature" FLOAT NOT NULL,
    "max_wind_speed" FLOAT NOT NULL,
    "max_wind_gust_speed" FLOAT NOT NULL,
    "dominant_wind_direction" SMALLINT NOT NULL,
    PRIMARY KEY (historical_reading_id),
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


CREATE TABLE "future_prediction"(
    "prediction_id" INTEGER GENERATED ALWAYS AS IDENTITY,
    "date" DATE NOT NULL,
    "location_id" INTEGER NOT NULL,
    "mean_temperature" FLOAT NOT NULL,
    "max_temperature" FLOAT NOT NULL,
    "min_temperature" FLOAT NOT NULL,
    "total_rainfall" FLOAT NOT NULL,
    "mean_wind_speed" FLOAT NOT NULL,
    "max_wind_speed" FLOAT NOT NULL,
    PRIMARY KEY (prediction_id),
    FOREIGN KEY (location_id) REFERENCES locations(location_id)
);

