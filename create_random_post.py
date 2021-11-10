import requests
from bs4 import BeautifulSoup


def create_random_post():
    url = 'https://ru.wikipedia.org/wiki/%D0%A1%D0%BB%D1%83%D0%B6%D0%B5%D0%B1%D0%BD%D0%B0%D1%8F:%D0%A1%D0%BB%D1%83%D1%87%D0%B0%D0%B9%D0%BD%D0%B0%D1%8F_%D1%81%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    content = soup.find_all('p')
    title = soup.find('h1', class_='firstHeading')
    content_str = ''
    title_str = title.text
    for i in content:
        content_str += i.text
    try:
        src_img = []
        main_image = soup.findAll(class_="infobox-image") + \
                    soup.findAll(class_="thumb")
        for i in main_image:
            img = i.find('img')
            src_img.append(img.get('src'))
    except AttributeError:
        src_img = []
    return[title_str, content_str, src_img]



