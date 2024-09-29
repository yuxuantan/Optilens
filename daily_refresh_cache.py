import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# visit optilens.streamlit.app?run_daily_refresh=yes_please using a browser and wait until daily refresh completed is shown in the html

# url = "http://localhost:8501/?run_daily_refresh=yes_please"
url = "https://optilens.streamlit.app/?run_daily_refresh=yes_please"

# Set up Chrome options for headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--enable-javascript")  # Ensure JavaScript is enabled
chrome_options.add_argument("--window-size=1920,1080")  # Set window size to ensure all content is visible
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")



# Set up the WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

try:
    # Visit the URL
    driver.get(url)

    # Wait until the "daily refresh completed" message appears
    while True:
        try:
            print("try")
            # print(driver.page_source)
            progress_text = driver.find_element(By.TAG_NAME, "h2").text.lower()
            print(progress_text)
            completion_text = driver.find_element(By.TAG_NAME, "h1").text.lower()
            if "daily refresh completed" in completion_text:
                print("Daily refresh completed")
                break
        except Exception as e:
            print("except")
            # print(f"Error: {str(e)}")
            pass
        time.sleep(3)  # Wait for 30 seconds before checking again
finally:
    driver.quit()
