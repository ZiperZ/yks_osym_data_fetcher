from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
import json
import os
import threading
from collections import defaultdict
from yok_utils import match_school, subject_info
import colorama

print('This tool is designed for fetching data from yok atlas')
print('Please enter all necessary data\n')
# ask the user for year
year = int(input('the year of data (only 2019-2020-2021-2022): '))
if not (year>=2019 and year<=2022):
    print('Invalid year')
    raise 'input failed'
MAX_RANKING = int(input('max ranking [0, 300,000]: ').replace(',', ''))
if not (MAX_RANKING>=0 ):
    print('Invalid ranking constraint')
    raise 'input failed'

# ask the user for desired schools
desired_schools = []
done = False
print('\nPlease enter which schools you want')
print('Algorithm works by strict comparing')
print('[!] Use only uppercase letters')
while True:
    school_name = input('Name of High School (enter nothing to finish): ')
    if not school_name.replace(' ', ''):
        done = True
        break
    if not school_name.isupper():
        print('Please only enter school name uppercase (previous names retained!)')
    desired_schools.append(school_name)
out_filename = f'yok_data_{year}.json'
print(f'Fetched data will be written in ${out_filename}')

colorama.init()
def print_progress():
    loading_characters = ['-', '/', '|', '\\']
    print_progress.timer = (print_progress.timer+1) % len(loading_characters)
    character = loading_characters[print_progress.timer]
    BAR_LENGTH = 30
    l = int(BAR_LENGTH*print_progress.progress)
    print('YÖK ATLAS Daten')
    print('Warten Sie mal bitte, wir nehmen daten...')
    print(character + ' ' + (colorama.Fore.GREEN + '█'*l + colorama.Fore.RED + '░'*(BAR_LENGTH-l)) + colorama.Fore.GREEN + f' {print_progress.progress*100:.1f}%' + colorama.Fore.WHITE)
print_progress.timer = 0
print_progress.progress = 0

if __name__ == '__main__':
    subject_ids = []

    if os.path.exists('./university_ids.json') and (json_data := json.load(open('./university_ids.json'))) and int(json_data['MAX_RANKING']) == MAX_RANKING:
        print('[!] USING DATA FROM "university_ids.json"')
        subject_ids = json_data['ids']
    else:
        # adjust ranking slidebar
        driver = webdriver.Chrome()
        driver.get('https://yokatlas.yok.gov.tr/tercih-sihirbazi-t4-tablo.php?p=say')

        right_button = driver.find_element(By.CSS_SELECTOR, '#bs-range > span:nth-child(3)')
        
        if MAX_RANKING > 0:
            slider = driver.find_element(By.CSS_SELECTOR, '#bs-range')
            width = slider.size['width']
            offset = (MAX_RANKING/400_000)*width
            ActionChains(driver, duration=100).click_and_hold(right_button).move_by_offset(-width+int(offset), 0).release().perform()

        dropdownbox = driver.find_element(By.CSS_SELECTOR, '#mydata_length > label > select')
        dropdownbox.click()
        dropdownbox.find_element(By.CSS_SELECTOR, 'option[value=\"100\"]').click()
        WebDriverWait(driver, timeout=5).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, '#mydata > tbody > tr')) >= 100)

        # gather university ids by traversing through the pages
        while True:
            rows = driver.find_elements(By.CSS_SELECTOR, '#mydata > tbody > tr')
            if not rows:
                break

            done = False
            for i in rows:
                subject_id = i.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').text
                subject_ids.append(subject_id)
            if done:
                break

            upper_code = rows[0].find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').text
            if (button := WebDriverWait(driver, timeout=5).until(lambda d: d.find_element(By.CSS_SELECTOR, '#mydata_next > a'))).get_attribute('class').split(' ').count('disabled') == 0:
                button.click()
            else:
                break
            def foo(d, upper_code):
                first_element = d.find_element(By.CSS_SELECTOR, '#mydata > tbody > tr:nth-child(1) > td:nth-child(2) > a')
                try:
                    return first_element.text != upper_code
                except:
                    return True
            try:
                WebDriverWait(driver, timeout=15).until(lambda d: foo(d, upper_code))
            except:
                break
        driver.close()
        # save ids
        json.dump(obj={ 'MAX_RANKING': MAX_RANKING, 'ids': subject_ids }, fp=open('./university_ids.json', 'w'))

    # from university ids, retrieve universities with target school
    data = defaultdict(list)
    print_progress.progress = 0
    for i, subject_id in enumerate(subject_ids):
        print_progress.progress = i/len(subject_ids)
        print_progress()
        if (r := match_school(subject_id, desired_schools, year)):
            for j in r:
                data[j].append(subject_info(subject_id, year))
    print_progress.progress = 1
    json.dump(obj=data, fp=open(out_filename, 'w'), indent=4)