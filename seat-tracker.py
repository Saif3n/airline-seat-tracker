import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from flask import Flask, request, jsonify
import requests
import time

# please note that send_error and send_email functions have not been defined as this code is for public viewing.

app = Flask(__name__)


def retry_click(new, wait):
    element = wait.until(new)

    try:
        element.click()
    except StaleElementReferenceException:
        # retry operation after small delay
        time.sleep(1)
        retry_click(new)

            

@app.route('/hiddenroute', methods=['POST'])
def check_availability():

    # desirable seats on 777-300, real endpoints have more options.
    couple_seats = ['34A','34B','34J','34K','35A','35B','35J','35K','58A','58B','58J','58K','59A','59B','59J','59K']
    neighboring_chars = {'A': 'B', 'B': 'A', 'J': 'K', 'K': 'J'}
    out_str = None
    
    try:
        data = request.get_json()

        booking_ref = data.get('booking_ref')
        family_name = data.get('family_name')
        client_id = data.get('client_id')
        departure_date = data.get('departure_date')
        email = data.get('email')



        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")


        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get('https://flightbookings.airnewzealand.co.nz/vmanage/actions/managebookingstart')
        driver.maximize_window()
        wait = WebDriverWait(driver, 3)


        
        span_element = wait.until(EC.presence_of_element_located((By.ID, "pb-ManageBookingRetrieve__bookingReference")))
        span_element.send_keys(booking_ref)

        span_element = wait.until(EC.presence_of_element_located((By.ID, "pb-ManageBookingRetrieve__familyName")))
        span_element.send_keys(family_name)
     
    
        retry_click(EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(), 'Continue')]]")), wait)
        retry_click(EC.element_to_be_clickable((By.ID, "option-seatselect")), wait)

        span_elements = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "bui-SeatSelectSeat__seatnumber.bui-SeatSelectSeat__seatnumber--responsiveHide.bui-SeatSelectSeat__seatnumber--sm")))

        # Create an empty dictionary to store the extracted data
        seat_dict = {}

        for span_element in span_elements:
            seat_number = span_element.text
            
            if seat_number in couple_seats:
                seat_dict[seat_number] = None

        valid_pairs=[]

        # loop through the couple_seats list
        for i in range(len(couple_seats)):

            seat = couple_seats[i]

            # get the number from the seat string (remove letter)
            number = seat[:-1]

            # prevent out of bounds
            if i + 1 < len(couple_seats) and couple_seats[i + 1].startswith(number):

                # gets last letters and checks with neighbouring chars last letter
                if couple_seats[i + 1][-1] == neighboring_chars[seat[-1]]:
                    valid_pairs.append((seat, couple_seats[i + 1]))

        for pair in valid_pairs:
            if pair[0] in seat_dict and pair[1] in seat_dict:
     
                out_str = pair[0], "and", pair[1], "are available seats on your flight, book now!."

        if out_str is True:
            send_email(email, out_str)

            response = {
                'success': True,
                'message': 'Seats are available!',
            }

        else:
            response = {
                'success': False,
                'message': 'Seats are not available.',
            }

        driver.quit()

    except Exception as e:
        response = {
            'success': False,
            'message': f'Failed to check seats as the booking reference for {email} and {booking_ref} was invalid.',
            'error': str(e)
        }
        send_error(f'Failed to check seats as the booking reference for {email} and {booking_ref} was invalid.')
        send_email(email, 'hi')
        return jsonify(response, f'Failed to check seats as your booking reference or family name was invalid (Ref: {booking_ref}, Name: {family_name}), we have now deleted your information from our database of tracked flights. Please feel free to track another flight.')
    return response


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
