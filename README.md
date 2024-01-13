# Scoracle

## Overview

Scoracle is a Django-based web application designed to provide soccer match predictions through statistical analysis. The project leverages technologies such as Django for web development, BeautifulSoup for web scraping, and Scipy for Poisson distribution calculations.

## Project Structure

- **scoracle/:** Django application directory.
  - **views.py:** Contains views and logic for handling various functionalities.

## Functionalities

1. **Home Page (`perdaypredictions/`):** Displays information about new visitors and serves as an entry point for users.

2. **League Prediction (`leagueprediction/`):** Provides predictions based on user-selected soccer leagues, fetching data through web scraping.

3. **Contact Form (`contact/`):** Allows users to submit messages via a contact form, triggering email notifications.

4. **Outcome Page (`outcome/`):** Displays predictions for the current day, including match outcomes and goal probabilities.

5. **XPrediction Page (`xprediction/`):** Performs predictions for upcoming matches, storing results in the database.

6. **XPredict Page (`xpredict/`):** Fetches data for upcoming matches, performs predictions, and stores results.

7. **Past Predictions Page (`pastpredictions/`):** Displays a list of past predictions, ordered by date.

8. **VIP Section (`vipsection/`):** Placeholder for a VIP section.

## Technologies Used

- **Django:** Web framework for building the application.
- **BeautifulSoup:** Web scraping library for data extraction.
- **Requests:** HTTP library for making web requests.
- **Scipy:** Used for Poisson distribution calculations.
- **JSON:** Utilized for working with JSON data.
- **Django's send_mail and redirect functions:** Handling email notifications and page redirects.

