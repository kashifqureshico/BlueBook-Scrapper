import os
import time
import csv
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# Function to scrape data for a single account
def scrape_account(account_num):
    # Initialize Chrome options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Add Tor proxy settings
    chrome_options.add_argument('--proxy-server=socks5://127.0.0.1:9050')

    # Initialize the WebDriver
    driver = webdriver.Chrome(options=chrome_options)

    try:
        website = f'https://www.thebluebook.com/iProView/{account_num}/crawford-tracey-corp/subcontractors/locations-contacts/'

        # Open the website for the current account
        driver.get(website)

        # Wait for the contact page to load completely
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="locationsPage-1"]/div/div[1]/div/div[1]/h3')))
        except TimeoutException:
            return None

        # Scrape specific text using the provided XPaths
        account_name = driver.find_element(By.XPATH, '//*[@id="locationsPage-1"]/div/div[1]/div/div[1]/h3').text
        address = driver.find_element(By.XPATH, '//*[@id="locationsPage-1"]/div/div/div/div[1]/div/div/div[1]').text

        try:
            acc_number_element = driver.find_element(By.XPATH, '//*[@id="locationsPage-1"]/div/div[1]/div/div[1]/div/div[1]/div[2]/div[1]/a/span')
            if acc_number_element.text == 'View Phone':
                # Scroll to the element
                action = ActionChains(driver)
                action.move_to_element(acc_number_element).perform()

                # C+lick the element to reveal the phone number
                driver.execute_script("arguments[0].click();", acc_number_element)
                time.sleep(2)  # Wait for the number to load

                # Check if FaceTime modal appears
                is_facetime_modal = False
                try:
                    facetime_modal = driver.find_element(By.XPATH, '//*[@id="URLbar"]/div/div[2]/div/div/div/div')
                    if facetime_modal.is_displayed():
                        is_facetime_modal = True
                except NoSuchElementException:
                    pass

                # If it's FaceTime modal, go back and try a different approach
                if is_facetime_modal:
                    # Go back to the previous page
                    driver.back()
                    return None
                else:
                    # Find the element containing the phone number
                    acc_number_element = driver.find_element(By.XPATH, '//*[@id="locationsPage-1"]/div/div/div/div[1]/div/div/div[2]/div[1]/a/span[2]')
            acc_number = acc_number_element.text
        except NoSuchElementException:
            acc_number = None
        company_info = driver.find_element(By.XPATH, '//*[@id="companyInfoSection"]/div/ul').text

        # Initialize website variable
        website = None

        # Scrape website if available
        try:
            website_element = driver.find_element(By.XPATH, '//*[@id="locationsPage-1"]/div/div[1]/div/div[1]/div/div[1]/div[3]/a')
            website = website_element.get_attribute('href')
        except NoSuchElementException:
            pass

        # Scrape industry if available
        try:
            industry_element = driver.find_element(By.XPATH, '//*[@id="proViewBreadCrumbs"]/a[3]')
            industry = industry_element.text
        except NoSuchElementException:
            industry = ''

        # Scrape contacts
        contacts = []
        for i in range(1, 8):  # There are 7 contacts based on provided XPaths
            name_xpath = f'//*[@id="keyContactSection"]/div/div[1]/div[{i}]/div/div/div/div/button'
            title_xpath = f'//*[@id="keyContactSection"]/div/div[1]/div[{i}]/div/div/div/div/div[1]'
            number_xpath = f'//*[@id="keyContactSection"]/div/div[1]/div[{i}]/div/div/div/div/div[2]/a/span'

            try:
                name = driver.find_element(By.XPATH, name_xpath).text
                title = driver.find_element(By.XPATH, title_xpath).text

                # Check if the text is "View Phone"
                number_element = driver.find_element(By.XPATH, number_xpath)
                if number_element.text == 'View Phone':
                    # Scroll to the element
                    action = ActionChains(driver)
                    action.move_to_element(number_element).perform()

                    # Click the element to reveal the phone number
                    driver.execute_script("arguments[0].click();", number_element)
                    time.sleep(2)  # Wait for the number to load

                    # Check if FaceTime modal appears
                    is_facetime_modal = False
                    try:
                        facetime_modal = driver.find_element(By.XPATH, '//*[@id="URLbar"]/div/div[2]/div/div/div/div')
                        if facetime_modal.is_displayed():
                            is_facetime_modal = True
                    except NoSuchElementException:
                        pass

                    # If it's FaceTime modal, skip this contact
                    if is_facetime_modal:
                        continue
                    else:
                        # Find the element containing the phone number
                        number_element = driver.find_element(By.XPATH, f'//*[@id="keyContactSection"]/div/div[1]/div[{i}]/div[1]/div/div/div/div[2]/a[1]/span[2]')
                number = number_element.text

                contacts.append({'Name': name, 'Title': title, 'Number': number})
            except NoSuchElementException:
                continue

        # Return the scraped data
        return {'account_num': account_num, 'account_name': account_name, 'address': address, 'acc_number': acc_number, 'company_info': company_info, 'website': website, 'industry': industry, 'contacts': contacts}

    finally:
        driver.quit()

# Set the directory to save the CSV file
save_dir = '/Users/safi.uddin/Desktop/bb_scrape'
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

# Open the CSV file in write mode
with open(os.path.join(save_dir, 'contacts.csv'), 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['ID', 'Name', 'Title', 'Number', 'Account Name', 'Address', 'Account number', 'Company Info', 'Website', 'Industry']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # Define the range of accounts
    account_range = range(1780000,1785000)

    # Initialize ThreadPoolExecutor with defined number of workers
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        # Submit scraping tasks
        futures = {executor.submit(scrape_account, account_num): account_num for account_num in account_range}

        # Iterate over completed tasks
        for future in concurrent.futures.as_completed(futures):
            account_num = futures[future]
            try:
                result = future.result()
                if result:  # Check if scraping was successful
                    if not result['contacts']:
                        writer.writerow({'ID': result['account_num'], 'Name': '', 'Title': '', 'Number': '', 'Account Name': result['account_name'], 'Address': result['address'], 'Account number': result['acc_number'], 'Company Info': result['company_info'], 'Website': result['website'], 'Industry': result['industry']})
                    for contact in result['contacts']:
                        writer.writerow({'ID': result['account_num'], 'Name': contact['Name'], 'Title': contact['Title'], 'Number': contact['Number'], 'Account Name': result['account_name'], 'Address': result['address'], 'Account number': result['acc_number'], 'Company Info': result['company_info'], 'Website': result['website'], 'Industry': result['industry']})
            except Exception as e:
                print(f"Failed to scrape account {account_num}: {e}")

# Delay to ensure all threads finish before quitting
time.sleep(5)
