from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
from selenium.webdriver.chrome.options import Options
from flask import request
app = Flask(__name__)

CHROME_DRIVER_PATH = "./chromedriver.exe"
my_date_format = "%b %d, %Y"
@app.route('/', methods=['GET', 'POST'])
def scrape_youtube_videos():
    driver =None
    try:
        channel_name = str(request.args.get('channel_name'))
        n_videos = int(request.args.get('n_videos'))
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=chrome_options)
        url_to_channel = f"https://www.youtube.com/{channel_name}/videos"
        driver.get(url_to_channel)

        scroll_position = 0
        scroll_increment = 2000
        num_scrolls = (n_videos -1)//20 +1
        for _ in range(num_scrolls):
            scroll_position += scroll_increment
            driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            time.sleep(0.5)

        video_links = []
        video_xpath = "//a[@class='yt-simple-endpoint inline-block style-scope ytd-thumbnail']"
        link_elements = driver.find_elements(by="xpath", value=video_xpath)
        video_links = [i.get_attribute('href') for i in link_elements if i is not None]

        scraped_video_info = []
        videos_scraped = 0  

        for video_url in video_links:
            if video_url is not None:
                driver.get(video_url)
                try:
                    wait = WebDriverWait(driver, 2)
                    expand_button = wait.until(EC.presence_of_element_located((By.XPATH, "//tp-yt-paper-button[@id='expand']")))
                    expand_button.click()
                    meta_data_xpath = "//div[@class='style-scope ytd-watch-metadata']/yt-formatted-string/span[3]"
                    data_stamp = driver.find_element(by='xpath', value=meta_data_xpath).text

                    try:
                        parsed_date_stamp = datetime.strptime(data_stamp, my_date_format)
                    except ValueError:
                        parsed_date_stamp = 'live or not available'
                    scraped_video_info.append({
                        "url": video_url,
                        "uploaded_date": parsed_date_stamp.strftime(my_date_format)
                    })
                    videos_scraped += 1  

                    if videos_scraped >= n_videos:
                        break  

                except Exception as e:
                    pass

                if videos_scraped >= n_videos:
                    break 

        return jsonify(scraped_video_info)

    except Exception as e:
        return jsonify({"error": str(e)})

    finally:
        driver.quit()

if __name__ == '__main__':
    app.run(debug=True)

