import csv
import re
import torch                
from transformers import AutoTokenizer, AutoModelWithLMHead
from time import sleep
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import selenium.webdriver as webdriver

# Data storage
data = []

# Function to extract data from each tweet card
def extractor(card):
    try:
        name = card.find_element(By.XPATH, './div/div/div[2]/div[2]/div[1]//span/span').text
        twthandle = card.find_element(By.XPATH, './/span[contains(text(), "@")]').text
        tweet_text = card.find_element(By.XPATH, './div/div/div[2]/div[2]/div[2]').text
        data.append((name, twthandle, tweet_text))
    except NoSuchElementException:
        pass

# Set up Twitter topics for testing
topics = ["AI taking jobs", "AI art stealing", "Is Alexa good", "Mahindra car reviews", "Honda car reviews",
          "Human gene editing", "Cryptocurrency reliability", "Climate change", "Driverless cars legality",
          "Electric cars", "Marijuana legalization", "Alcohol ban India"]

# User input for topic selection
topic = input("Enter a topic>>> ")

# Browser settings
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.69'
edge_driver_path = './msedgedriver.exe'
edge_service = Service(edge_driver_path)
edge_options = Options()
edge_options.add_argument(f'user-agent={user_agent}')

# Start the browser
driver = webdriver.Edge(service=edge_service, options=edge_options)
driver.get('https://www.twitter.com/login')
driver.maximize_window()

# Log in to Twitter
try:
    sleep(5)
    username_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="layers"]/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div/div/div/div[4]/label/div/div[2]/div/input'))
    )
    username_field.send_keys("", Keys.ENTER)
    sleep(5)
    # driver.find_element(By.XPATH, '//*[@id="layers"]/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div/div/div/div[6]/div/span/span').click()
    password_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="layers"]/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div/div[3]/div/label/div/div[2]/div[1]/input'))
    )
    password_field.send_keys('', Keys.ENTER)
    sleep(6)
except (NoSuchElementException, TimeoutException):
    print("Error during login")
    driver.quit()

# Search for the topic on Twitter
try:
    driver.get("https://twitter.com/home")
    sleep(3)
    search_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//input[@data-testid="SearchBox_Search_Input"]'))
    )
    search_box.send_keys(topic)
    search_box.send_keys(Keys.ENTER)

    # Loop for scrolling and data extraction
    num = 1
    flag = True
    while num <= 50 and flag:
        print("On loop no ->>", num)
        sleep(2)
        num += 1
        tries = 0
        last_pos = driver.execute_script('return window.pageYOffset;')
        cards = driver.find_elements(By.XPATH, '//article[@data-testid="tweet"]')
        for card in cards[-15:]:
            extractor(card)

        # Save data to CSV file
        with open(topic + '.csv', 'a', newline='', encoding='utf-8') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerows(data)
            data = []

        # Scroll and check for new content
        while driver.execute_script('return window.pageYOffset;') == last_pos:
            if tries >= 6:
                flag = False
                break
            else:
                driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                sleep(3)
                tries += 1
                print("Current try no. ---> ", tries)

    print("Total tweets collected:", len(data))

except Exception as e:
    print("An error occurred:", e)
finally:
    driver.quit()

WHITESPACE_HANDLER = lambda k: re.sub('\s+', ' ', re.sub('\n+', ' ', k.strip()))
article_text = ""

with open(f"{topic}.csv", "r", encoding="utf-8") as csvfile:
    csvreader = csv.reader(csvfile)
    for row in csvreader:
        if len(row) > 2:  # Assuming the tweet text is in the third column
            article_text += " " + row[2]

tokenizer = AutoTokenizer.from_pretrained('t5-base')                        
model = AutoModelWithLMHead.from_pretrained('t5-base', return_dict=True)   

inputs = tokenizer.encode("summarize: " + article_text,                  
return_tensors='pt',              
max_length=512,             
truncation=True)    

summary_ids = model.generate(inputs, max_length=250, min_length=80, length_penalty=5., num_beams=2)   
summary = tokenizer.decode(summary_ids[0]) 
print(summary)