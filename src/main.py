import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from apify import Actor


def init_driver():
    """Configure and return a Selenium Chrome driver."""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)


def scrape_account(driver, account_url):
    """Scrape one BlueBook company profile given its URL."""

    driver.get(account_url)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="locationsPage-1"]/div/div[1]/div/div[1]/h3')
            )
        )
    except TimeoutException:
        return None

    # Basic info
    account_name = driver.find_element(By.XPATH, '//*[@id="locationsPage-1"]/div/div[1]/div/div[1]/h3').text
    address = driver.find_element(By.XPATH, '//*[@id="locationsPage-1"]/div/div/div/div[1]/div/div/div[1]').text

    # Phone
    try:
        acc_number_element = driver.find_element(
            By.XPATH,
            '//*[@id="locationsPage-1"]/div/div[1]/div/div[1]/div/div[1]/div[2]/div[1]/a/span'
        )
        if acc_number_element.text == 'View Phone':
            ActionChains(driver).move_to_element(acc_number_element).perform()
            driver.execute_script("arguments[0].click();", acc_number_element)
            time.sleep(2)
            acc_number_element = driver.find_element(
                By.XPATH,
                '//*[@id="locationsPage-1"]/div/div/div/div[1]/div/div/div[2]/div[1]/a/span[2]'
            )
        acc_number = acc_number_element.text
    except NoSuchElementException:
        acc_number = None

    # Company info
    try:
        company_info = driver.find_element(By.XPATH, '//*[@id="companyInfoSection"]/div/ul').text
    except NoSuchElementException:
        company_info = ""

    # Website
    try:
        website_element = driver.find_element(
            By.XPATH, '//*[@id="locationsPage-1"]/div/div[1]/div/div[1]/div/div[1]/div[3]/a'
        )
        website = website_element.get_attribute("href")
    except NoSuchElementException:
        website = None

    # Industry
    try:
        industry = driver.find_element(By.XPATH, '//*[@id="proViewBreadCrumbs"]/a[3]').text
    except NoSuchElementException:
        industry = ""

    # Contacts
    contacts = []
    for i in range(1, 8):
        try:
            name = driver.find_element(
                By.XPATH,
                f'//*[@id="keyContactSection"]/div/div[1]/div[{i}]/div/div/div/div/button'
            ).text
            title = driver.find_element(
                By.XPATH,
                f'//*[@id="keyContactSection"]/div/div[1]/div[{i}]/div/div/div/div/div[1]'
            ).text
            number_element = driver.find_element(
                By.XPATH,
                f'//*[@id="keyContactSection"]/div/div[1]/div[{i}]/div/div/div/div/div[2]/a/span'
            )
            if number_element.text == "View Phone":
                ActionChains(driver).move_to_element(number_element).perform()
                driver.execute_script("arguments[0].click();", number_element)
                time.sleep(2)
                number_element = driver.find_element(
                    By.XPATH,
                    f'//*[@id="keyContactSection"]/div/div[1]/div[{i}]/div[1]/div/div/div/div[2]/a[1]/span[2]'
                )
            number = number_element.text
            contacts.append({"Name": name, "Title": title, "Number": number})
        except NoSuchElementException:
            continue

    # Extract account_id from URL
    account_id_match = re.search(r"/iProView/(\d+)/", account_url)
    account_id = int(account_id_match.group(1)) if account_id_match else None

    return {
        "account_num": account_id,
        "account_name": account_name,
        "address": address,
        "acc_number": acc_number,
        "company_info": company_info,
        "website": website,
        "industry": industry,
        "contacts": contacts,
        "source_url": account_url,
    }


def collect_company_links(driver, keyword, location, max_companies=50):
    """Collect company profile URLs from BlueBook search results."""
    search_url = f"https://www.thebluebook.com/search.html?region={location}&trade={keyword}"
    driver.get(search_url)

    company_urls = []
    while len(company_urls) < max_companies:
        # Wait for company cards to load
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".companyInfo a"))
            )
        except TimeoutException:
            break

        links = driver.find_elements(By.CSS_SELECTOR, ".companyInfo a")
        for link in links:
            href = link.get_attribute("href")
            if href and "/iProView/" in href and href not in company_urls:
                company_urls.append(href)
                if len(company_urls) >= max_companies:
                    break

        # Try pagination (next button)
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, "a.next")
            if "disabled" in next_button.get_attribute("class"):
                break
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(3)
        except NoSuchElementException:
            break

    return company_urls


# === Apify entrypoint ===
async def main():
    await Actor.init()
    dataset = await Actor.open_dataset()

    input_data = await Actor.get_input() or {}
    keyword = input_data.get("keyword", "subcontractors")
    location = input_data.get("location", "New York")
    max_companies = int(input_data.get("max_companies", 50))

    driver = init_driver()
    try:
        print(f"➡️ Searching for '{keyword}' in '{location}' (limit {max_companies})")
        company_links = collect_company_links(driver, keyword, location, max_companies)
        print(f"Found {len(company_links)} companies.")

        for url in company_links:
            try:
                result = scrape_account(driver, url)
                if result:
                    await dataset.push_data(result)
                    print(f"✅ Scraped {result['account_name']}")
            except Exception as e:
                print(f"⚠️ Failed to scrape {url}: {e}")

    finally:
        driver.quit()

    await Actor.exit()
