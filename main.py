import requests, statistics, nltk, re
from collections import Counter
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from pywebio import input, output, start_server, session
import pandas as pd
import matplotlib.pyplot as plt
from cutecharts.charts import Line

salary_data = []
familly_data = []
keywords_data = []
freq_words = []

def count_freq_words(data):
    word_counts = Counter(data)
    for word, count in word_counts.items():
        freq_words.append(f"{word}: {count}")

def salary_analysis(data):
    data_withoutNone = [x for x in data if x is not None]
    chart = Line("Общий график зарплат")
    chart.set_options(labels=[f"{i+1}" for i in range(len(data_withoutNone))] ,x_label="Количество вакансий", y_label="Уровень зарплат")
    chart.add_series("Line", data_withoutNone)
    chart.render()
    output.put_html(chart.render_notebook())
    output.put_text(f"Медианная зарпалата:      {statistics.median(data_withoutNone)}")
    output.put_text(f"Максимальная зарпалата:      {max(data_withoutNone)}")
    output.put_text(f"Минимальная зарпалата:      {min(data_withoutNone)}")
    sorted_freq_words = sorted(freq_words, key=lambda x: int(x.split(":")[1]), reverse=True)
    output.put_text(f"Список используемых слов {sorted_freq_words}")

def remove_stopwords(tokens):

    stop_words = set(stopwords.words('russian'))
    filtred_tokens = [token for token in tokens if token not in stop_words]
    keywords_data.append(filtred_tokens)
    return keywords_data

def neural_network_to_clear_data(data):
    nltk.download('punkt')
    nltk.download('stopwords')
    data_text = "".join(data)
    data_text = data_text.lower()
    data_text = re.sub(r'[^a-zA-Zа-яА-Я0-9]', ' ', data_text)
    remove_stopwords(data_text)
    words = data_text.split()
    count_freq_words(words)

def get_vacancies(keyword):
    output.put_row (
        [
            output.put_buttons(["Анализ вакансий"], onclick=[analysis_vacancies])
        ]
    )
    output.put_text("Поиск ваканский...")
    url = "https://api.hh.ru/vacancies"
    params = {
        "text": keyword,
        "area": 1,  # Specify the desired area ID (1 is Moscow)
        "per_page": 80,  # Number of vacancies per page
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        vacancies = data.get("items", [])
        num_vacancies = len(vacancies)

        if num_vacancies > 0:
            for i, vacancy in enumerate(vacancies):
                vacancy_id = vacancy.get("id")
                vacancy_title = vacancy.get("name")
                vacancy_url = vacancy.get("alternate_url")
                vacancy_snippet = vacancy.get("snippet")
                vacancy_snippet = str(vacancy_snippet["responsibility"])
                vacancy_snippet = vacancy_snippet.replace("<highlighttext>", "")
                vacancy_snippet = vacancy_snippet.replace("</highlighttext>", "")
                familly_data.append(vacancy_snippet)
                vacancy_salary = vacancy.get("salary")
                if vacancy_salary is None:
                    vacancy_salary = "Не указана"
                    vacancy_currency = "Неизвестно"
                elif isinstance(vacancy_salary, int):
                    vacancy_currency = "Неизвестно"
                else:
                    vacancy_currency = vacancy_salary['currency']
                    vacancy_salary = vacancy_salary['from']
                    salary_data.append(vacancy_salary)
                company_name = vacancy.get("employer", {}).get("name")

                output.put_text(f"ID: {vacancy_id}")
                output.put_text(f"Название: {vacancy_title}")
                output.put_text(f"Зарплата: {vacancy_salary}")
                output.put_text(f"Валюта: {vacancy_currency}")
                output.put_text(f"Компания: {company_name}")
                output.put_text(f"Требования: {vacancy_snippet}")
                output.put_text(f"URL: {vacancy_url}")
                output.put_text("")  # Add an empty line for separation

                if i < num_vacancies - 1:
                    output.put_text("---------")  # Add separation line
        else:
            output.put_text("No vacancies found.")
    else:
        output.put_text(f"Request failed with status code: {response.status_code}")


def analysis_vacancies():
    output.clear()
    output.put_row(
        [
            output.put_buttons(["Вернуться назад"], onclick=[search_vacancies], )
        ]
    )
    salary_analysis(salary_data)


def search_vacancies():
    keyword = input.input("Введите название вакансии для анализа:", type=input.TEXT)
    output.clear()
    get_vacancies(keyword)
    neural_network_to_clear_data(familly_data)

if __name__ == '__main__':
    start_server(search_vacancies, port=8080)