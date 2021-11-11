import requests
from bs4 import BeautifulSoup


def create_random_post():
    url = 'https://ru.wikipedia.org/wiki/%D0%A1%D0%BB%D1%83%D0%B6%D0%B5%D0%B1%D0%BD%D0%B0%D1%8F:%D0%A1' \
          '%D0%BB%D1%83%D1%87%D0%B0%D0%B9%D0%BD%D0%B0%D1%8F_%D1%81%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')

    title = soup.find('h1', class_='firstHeading')
    title_str = title.text

    content_str = ''
    for i in soup.find_all('p'):
        content_str += i.text

    src_img = []
    try:
        main_image = soup.findAll(class_="infobox-image") + \
                     soup.findAll(class_="thumb")
        for i in main_image:
            img = i.find('img')
            src_img.append(img.get('src'))
    except AttributeError:
        pass

    return [title_str, content_str, src_img]


def check_user_status(current_user):
    return str(current_user.status) if current_user.is_authenticated else None
