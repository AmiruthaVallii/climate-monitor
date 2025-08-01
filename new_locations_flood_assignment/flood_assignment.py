from ..db.seed_flood_area_assignment import get_flood_area_codes, RADIUS, get_flood_area, match_flood_area_codes_to_flood_area_id, insert_into_flood_assignment
import pandas as pd
from dotenv import dotenv_values


def lambda_handler(event: dict, context) -> dict:  # pylint: disable=unused-argument
    """
    Uploads flood_assignment for given location_id, latitude and longitutde.
    Parameters:
        event: Dict containing the location_id, start_date and end_date 
            e.g. {"location_id": 1, "latitude": 51.507351, "longitude": -0.127758}
        context: Lambda runtime context
    Returns:
        Dict containing status message
    """
    config_values = dotenv_values()
    codes_for_new_location = get_flood_area_codes(
        event['latitude'], event['longitude'])
    df = pd.DataFrame(
        {'location_id': event['location_id'], 'flood_area_codes': [codes_for_new_location]})
    flood_dict = get_flood_area(config_values)
    matched_df = match_flood_area_codes_to_flood_area_id(df, flood_dict)
    return (df)

    # return {
    #     "statusCode": 200,
    #     "message": "Future weather data successfully inserted."
    # }


if __name__ == "__main__":
    out = lambda_handler({"location_id": 1,
                          "latitude": 51.507351,
                          "longitude": -0.127758,
                          "start_date": "2040-01-06",
                          "end_date": "2040-01-07"},
                         "context")
    print(out)
