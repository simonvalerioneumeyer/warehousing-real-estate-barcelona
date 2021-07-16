import pandas as pd
import requests
import base64
import json
from sqlalchemy import create_engine
import yaml
import os

# load yaml file:
with open(r'config.yml') as file:
    configs = yaml.load(file)

def get_has_parking_space(str_of_dict, var):
    """
    This function parses out parking booleans
    """
    if pd.isnull(str_of_dict):
        return False
    else:
#         dict_ = ast.literal_eval(str_of_dict)
        return str_of_dict[var]

def get_oauth_token(configs):
    """
    This function returns the bearer token with given url and api-key.
    """
    message = os.getenv('apikey') + ':' + os.getenv('secret')
    auth = "Basic " + base64.b64encode(message.encode("ascii")).decode("ascii")
    headers_dic = {"Authorization": auth, "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"}
    params_dic = {"grant_type": "client_credentials", "scope": "read"}
    content = requests.post(configs['token_info']['url'], headers=headers_dic, params=params_dic)
    bearer_token = json.loads(content.text)['access_token']
    return bearer_token

def search_api(token, url):
    """
    This function takes a token and a url as an input, does one request and outputs the data as a dictionary.
    """
    headers = {'Content-Type': 'Content-Type: multipart/form-data;', 'Authorization': 'Bearer ' + token}
    content = requests.post(url, headers=headers)
    result = json.loads(content.text)
    return result

# Get the data from the API:
def update_api_idealista():
    """
    This function specifies filters on what to request from the api,
    performs as many requests as specified and creates a dataframe with the data.
    It then sends the data to the mysql database.
    """
    # initialize empty dataframe
    df_property = pd.DataFrame()

    for i in range(configs['api_filters']['limit']):
        url = ('https://api.idealista.com/3.5/' + configs['api_filters']['country'] +
               '/search?operation=' + configs['api_filters']['operation'] + #"&locale="+locale+
               '&maxItems=' + configs['api_filters']['max_items'] +
               '&order=' + configs['api_filters']['order'] +
               '&center=' + configs['api_filters']['center'] +
               '&distance=' + configs['api_filters']['distance'] +
               '&sinceDate=' + configs['api_filters']['sinceDate'] +
               '&propertyType=' + configs['api_filters']['property_type'] +
               '&sort=' + configs['api_filters']['sort'] +
               '&numPage=%s' +
               '&language=' + configs['api_filters']['language']) %(i)
        a = search_api(get_oauth_token(configs), url)
        df = pd.DataFrame.from_dict(a['elementList'])
        df_property = pd.concat([df_property, df])

    df_property = df_property.reset_index()
    print(f'Dataframe has the shape: {df_property.shape}')

    # Parse parking: Commented out for now, might introduce ex post, if needed
    df_property['isParkingSpaceIncludedInPrice'] = df_property.parkingSpace.apply(lambda x: get_has_parking_space(x, var = 'isParkingSpaceIncludedInPrice'))
    df_property['hasParkingSpace'] = df_property.parkingSpace.apply(lambda x: get_has_parking_space(x, var = 'hasParkingSpace'))

    # Filter out:
    df_property = df_property[['propertyCode',
                               'price',
                               'province',
                               'municipality',
                               'priceByArea',
                               'floor',
                               'size',
                               'rooms',
                               'bathrooms',
                               'exterior',
                               'distance',
                               'status',
                               'hasLift',
                               'propertyType',
                               'operation',
                               'hasParkingSpace',
                               'isParkingSpaceIncludedInPrice',
                               'address',
                               'district',
                               'neighborhood',
                               'latitude',
                               'longitude']].drop_duplicates('propertyCode')

    # Add the dataframe to the database:
    engine = create_engine('mysql+pymysql://seb:Pass_word@3.19.73.138:3306/idealista', echo=False)
    df_property.to_sql('property', con=engine, if_exists='append', index=False)
    return
