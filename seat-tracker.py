from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
import time

couple_seats = ['34A','34B','34J','34K','35A','35B','35J','35K','58A','58B','58J','58K','59A','59B','59J','59K']
neighboring_chars = {'A': 'B', 'B': 'A', 'J': 'K', 'K': 'J'}


booking_ref = input("Enter your booking reference: ")
family_name = input("Enter your family name: ")


options = Options()
options.add_experimental_option("detach", True)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

driver.get("https://flightbookings.airnewzealand.co.nz/vmanage/actions/managebookingstart")
driver.maximize_window()

wait = WebDriverWait(driver, 10)

def retry_click(new):
    element = wait.until(new)

    try:
        element.click()
    except StaleElementReferenceException:
        # Re-try the operation after a small delay
        time.sleep(1)
        retry_click(new)


span_element = wait.until(EC.presence_of_element_located((By.ID, "pb-ManageBookingRetrieve__bookingReference")))
span_element.send_keys(booking_ref)

span_element = wait.until(EC.presence_of_element_located((By.ID, "pb-ManageBookingRetrieve__familyName")))
span_element.send_keys(family_name)

retry_click(EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(), 'Continue')]]")))

retry_click(EC.element_to_be_clickable((By.ID, "option-seatselect")))

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
        # when I actually deployed this to a timer trigger, it sent a notification email, the print statement has been used as this script is a showcase.
        print(pair[0], "and", pair[1], "are valid seats, book now!.")