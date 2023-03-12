from bs4 import BeautifulSoup
import requests

# 2022 edition!!!!
def match_school(id: str, schools: list[str], year: int = 2022):
    response = requests.get('https://yokatlas.yok.gov.tr' + (f'/{year}' if year!=2022 else '') + f'/content/lisans-dynamic/1060.php?y={id}')
    soup = BeautifulSoup(response.text, features='html.parser')
    rows = soup.select('table > tbody > tr')[1:]
    result = []
    for i in rows:
        school_name = i.select_one('td:nth-child(1)').text
        for j in schools:
            if school_name.startswith(j):
                result.append(j)
    return result

def subject_info(id: str, year: int = 2022):
    n_retries = 0
    response = None
    while response is None and n_retries < 10:
        try:
            response = requests.get('https://yokatlas.yok.gov.tr' + (f'/{year}' if year!=2022 else '') + f'/content/lisans-dynamic/1000_1.php?y={id}')
        except:
            pass
    if n_retries >= 10:
        raise 'sunucu ölmüş ustam bune'

    soup = BeautifulSoup(response.text, features='html.parser')
    ranking = 0
    try:
        ranking = int(soup.select_one('table:nth-child(3) > tbody > tr:nth-child(3) > td.text-center.vert-align').text.replace('.', ''))
    except:
        pass
    return {
        'subject': soup.select_one('table:nth-child(1) > thead > tr > th > big').text,
        'university': soup.select_one('table:nth-child(1) > tbody > tr:nth-child(3) > td.text-center.vert-align').text,
        'faculty': soup.select_one('table:nth-child(1) > tbody > tr:nth-child(4) > td.text-center.vert-align').text,
        'ranking': ranking,
    }