### LIBRARIES ###

import requests
import re
import pandas as pd
import time
import numpy as np
import os
from bs4 import BeautifulSoup


### FUNCTIONS ###


# Name : paris_restaurant_list_scrapping
# Input expected : Number of the scrapped page(int)
# Output expected : Name of the restaurant and its url(dataframe)

def paris_restaurant_list_scrapping(page):
    # Scrapping of the data

    tripadvisor_root = 'https://www.tripadvisor.fr'
    url = '/Restaurants-g187147-oa{0}-Paris_Ile_de_France.html#EATERY_LIST_CONTENTS'.format(page)
    driver = requests.get(tripadvisor_root + url)
    content = BeautifulSoup(driver.content, "html.parser")

    # Data extraction

    restaurant_box = content.findAll('div', {'class': re.compile('^listing')})[1:]
    restaurant_box = [restaurant.find('div', {'class': 'title'}) for restaurant in restaurant_box]

    name = [name.find('a', {'class': 'property_title'}).text for name in restaurant_box]
    url = [tripadvisor_root + url.find('a', {'class': 'property_title'}).get('href') for url in restaurant_box]

    # Formatting of the result

    result = pd.DataFrame({'Name': name,
                           'Url': url})

    return result


# Name : restaurant_overview_scrapping
# Input expected : Web page content(BeautifulSoup)
# Output expected : Rating, number of comment, location and telephone number of the restaurant(dataframe)

def restaurant_overview_scrapping(content):

    # Data extraction

    rating = content.find('span',
                          {'class': 'restaurants-detail-overview-cards-RatingsOverviewCard__overallRating--nohTl'}).text
    comment_count = content.find('a', {
        'class': 'restaurants-detail-overview-cards-RatingsOverviewCard__ratingCount--DFxkG'}).text
    location = content.find('span', {
        'class': 'restaurants-detail-overview-cards-LocationOverviewCard__detailLinkText--co3ei'}).text
    telephone = content.find('a', {'href': re.compile('^tel:')}).text

    # Formatting of the result

    result = pd.DataFrame({'Rating': [rating],
                           'Comment_Count': [comment_count],
                           'Location': [location],
                           'Telephone': [telephone]})

    return result


# Name : restaurant_comments_scrapping
# Input expected : Web page content(BeautifulSoup)
# Output expected : Rating, number of comment, location and telephone number of the restaurant(dataframe)

def restaurant_comments_scrapping(content):

    # Data extraction

    review_box = content.findAll('div', {'class': 'review-container'})
    rating = [rating.find('span', {'class': re.compile('^ui_bubble')}).get('class')[1] for rating in review_box]
    comment_date = [date.find('span', {'class': 'ratingDate'}).get('title') for date in review_box]
    title = [title.find('span', {'class': 'noQuotes'}).text for title in review_box]
    comment = [comment.find('p', {'class': 'partial_entry'}).text for comment in review_box]
    visit_date = [visit_date.find('div', {'data-prwidget-name': 'reviews_stay_date_hsx'}).text for visit_date in
                  review_box]

    # Formatting of the result

    result = pd.DataFrame({'Rating': rating,
                           'Date': comment_date,
                           'Title': title,
                           'Comment': comment,
                           'Visit_date': visit_date})

    return result


# Name : clean_restaurants
# Input expected : Raw names and raw urls of the restaurants(dataframe)
# Output expected : Clean names and clean urls of the restaurants(dataframe)

def clean_restaurants(restaurants):

    # Cleansing of the names

    restaurants['Name'] = restaurants['Name'].str.strip()

    return restaurants


# Name : clean_restaurants_comments
# Input expected : Raw comments of the restaurants (dataframe)
# Output expected : Clean comments of the restaurants (dataframe)

def clean_restaurants_comments(restaurants_comments):

    # Cleansing of the ratings
    restaurants_comments['Rating'] = restaurants_comments['Rating'].apply(lambda rating: rating[-2])

    # Cleansing of the dates
    months = {'janvier': 'January',
              'février': 'February',
              'mars': 'March',
              'avril': 'April',
              'mai': 'May',
              'juin': 'June',
              'juillet': 'July',
              'août': 'August',
              'septembre': 'September',
              'octobre': 'October',
              'novembre': 'November',
              'décembre': 'December'
              }

    restaurants_comments['Date'] = restaurants_comments['Date'].replace(months, regex=True)
    restaurants_comments['Date'] = pd.to_datetime(restaurants_comments['Date'], format='%d %B %Y')
    restaurants_comments['Date'] = restaurants_comments['Date'].dt.strftime('%d/%m/%Y')

    # Cleansing of the titles
    restaurants_comments['Title'] = restaurants_comments['Title'].str.strip()
    wrong_values = {'\n': ' ', ' \| ': ', '}
    restaurants_comments['Title'] = restaurants_comments['Title'].replace(wrong_values, regex=True)

    # Cleansing of the comments
    restaurants_comments['Comment'] = restaurants_comments['Comment'].str.strip()
    wrong_values = {'\.{3}Plus': '...', '\n': ' ', ' \| ': ', '}
    restaurants_comments['Comment'] = restaurants_comments['Comment'].replace(wrong_values, regex=True)
    mask = restaurants_comments['Comment'].str.len() >= 300
    restaurants_comments['Comment'].loc[mask] = restaurants_comments['Comment'].loc[mask].apply(
        lambda x: str(x)[:297] + '...')

    # Cleansing of the visit dates
    restaurants_comments['Visit_date'] = restaurants_comments['Visit_date'].str.strip()
    restaurants_comments['Visit_date'] = restaurants_comments['Visit_date'].replace({'Date\sde\sla\svisite\s:\s': ''},
                                                                                    regex=True)
    restaurants_comments['Visit_date'] = restaurants_comments['Visit_date'].replace(months, regex=True)
    restaurants_comments['Visit_date'] = pd.to_datetime(restaurants_comments['Visit_date'], format='%B %Y',
                                                        errors='coerce')
    restaurants_comments['Visit_date'] = restaurants_comments['Visit_date'].dt.strftime('%d/%m/%Y')

    # Cleansing of the update dates
    restaurants_comments['Update_Date'] = time.strftime('%d/%m/%Y', time.gmtime())

    return restaurants_comments

# Name : clean_restaurants_overview
# Input expected : Raw overviews of the restaurants (dataframe)
# Output expected : Clean overviews of the restaurants (dataframe)

def clean_restaurants_overview(restaurants_overview):

    # Cleansing of the ratings
    restaurants_overview['Rating'] = restaurants_overview['Rating'].replace({',0': '', ',5': ''}, regex=True)

    # Cleansing of the comment counts
    restaurants_overview['Comment_Count'] = restaurants_overview['Comment_Count'].replace({'\s': '', 'avis': ''},
                                                                                          regex=True)

    # Cleansing of the address
    restaurants_overview['Address'] = restaurants_overview['Location'].str.extract('(.*[a-z]),\s')

    # Cleansing of the zipcodes
    restaurants_overview['ZIPCODE'] = restaurants_overview['Location'].str.extract('(\d{5})')
    restaurants_overview = restaurants_overview.drop('Location', axis=1)

    # Cleansing of the update dates
    restaurants_overview['Update_Date'] = time.strftime('%d/%m/%Y', time.gmtime())

    return restaurants_overview

# Name : main_restaurants_scrapping
# Input expected : Number of TripAdvisor page (int)
# Output expected : -

def main_restaurants_scrapping(nb_pages):

    # Initialization of the variables
    count = nb_pages
    every_time_left = []
    restaurants = pd.DataFrame()

    for page in range(0, nb_pages * 30, 30):

        # Scrappping of the data
        start = time.time()

        result = paris_restaurant_list_scrapping(page)
        restaurants = pd.concat([restaurants, result])

        end = time.time()

        # Printing of the advancement
        every_time_left.append(round((end - start)))
        time_left = np.round(np.mean(every_time_left) * count)

        print("\033[H\033[J")
        print('{0} pages de restaurants restantes.'.format(count))
        print('Fin du scrapping dans environ {0} secondes.'.format(time_left))

        count -= 1

    # Cleansing of the scrapped data
    restaurants = clean_restaurants(restaurants)

    # Saving of the data
    restaurants.to_csv('restaurants.csv', index=False)

# Name : main_restaurants_details_scrapping
# Input expected : Names of the restaurants and its url (dataframe)
# Output expected : -

def main_restaurants_details_scrapping(restaurants):

    # Look up of the existing files
    restaurants_overview_exists = os.path.exists('restaurants_overview.csv')
    restaurants_comments_exists = os.path.exists('restaurants_comments.csv')

    # Reject of the old scrapped data ( >= 7 days)
    if (restaurants_overview_exists == True and restaurants_comments_exists == True):

        restaurants_overview = pd.read_csv('restaurants_overview.csv', sep='|')
        restaurants_comments = pd.read_csv('restaurants_comments.csv', sep='|')

        now = time.strftime('%d/%m/%Y', time.gmtime())

        mask = pd.to_datetime(restaurants_overview['Update_Date']) - pd.to_datetime(now)
        mask = mask.dt.days < 7
        restaurants_overview = restaurants_overview.loc[mask]

        mask = pd.to_datetime(restaurants_comments['Update_Date']) - pd.to_datetime(now)
        mask = mask.dt.days < 7
        restaurants_comments = restaurants_comments.loc[mask]

        mask = restaurants['Url'].isin(restaurants_overview['Restaurant_Url'].tolist())
        restaurants = restaurants.loc[~mask]

    else:
        restaurants_overview = pd.DataFrame()
        restaurants_comments = pd.DataFrame()


    # Initialization of the variables
    every_time_left = []
    count = restaurants['Url'].count()

    for url in restaurants['Url'].tolist():

        start = time.time()

        # Scrapping of the web page content
        driver = requests.get(url)
        content = BeautifulSoup(driver.content, "html.parser")

        # Attempt of scrapping the overview of the restaurant
        try:
            overview_result = restaurant_overview_scrapping(content)
            overview_result = clean_restaurants_overview(overview_result)
            overview_result['Restaurant_Url'] = url
            restaurants_overview = pd.concat([restaurants_overview, overview_result], sort=False)
            restaurants_overview.to_csv('restaurants_overview.csv', index=False, sep='|')
        except:
            pass


        # Attempt of scrapping the comments of the restaurant
        try:
            comments_result = restaurant_comments_scrapping(content)
            comments_result = clean_restaurants_comments(comments_result)
            comments_result['Restaurant_Url'] = url
            restaurants_comments = pd.concat([restaurants_comments, comments_result], sort=False)
            restaurants_comments.to_csv('restaurants_comments.csv', index=False, sep='|')
        except:
            pass

        end = time.time()

        # Printing of the advancement
        every_time_left.append(round((end - start)))
        time_left = np.round(np.mean(every_time_left) * count)

        print("\033[H\033[J")
        print('{0} restaurants restants.'.format(count))
        print('Fin du scrapping dans environ {0} secondes.'.format(int(time_left)))

        count -= 1