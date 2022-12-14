from decimal import Decimal
import Database as db
from bs4 import BeautifulSoup
from bs4.element import Comment
import requests
import selenium.common.exceptions
import unidecode
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.support.wait import WebDriverWait
import json
import timeit

URL = "https://www.tudogostoso.com.br/categorias/"
PATH_DATA = "data/DATA.json"


def load_browser():
    global driver
    binary = FirefoxBinary('modules/firefox/firefox.exe')
    driver = webdriver.Firefox(executable_path=r"modules/geckodriver.exe", firefox_binary=binary)
    # driver.implicitly_wait(0.2)
    # driver.set_page_load_timeout(1000)
    # driver = webdriver.Chrome(executable_path=r"modules/chromedriver.exe")


def open_link(url):
    driver.delete_all_cookies()
    driver.get(url)
    WebDriverWait(driver, 0.5)


def get_categories():
    open_link(URL)
    links = []
    names = []

    links_web_driver = driver.find_elements(By.XPATH, '//a[@class="tags"] | //a[h2[@class="box-title"]]')

    for link in links_web_driver:
        href = link.get_attribute('href')
        name = link.get_attribute('innerText')
        names.append(name)
        links.append(href)

    driver.delete_all_cookies()
    return links, names


def read_data_json():
    with open(PATH_DATA, "rb") as file:
        data = json.load(file)
    return data


def read_ignored_words():
    # LOAD IGNORED WORD
    with open("data/IgnoredWords.json", "r", encoding="utf-8") as file:
        ignored_words = json.load(file)

    return ignored_words


def write_data_json(data):
    with open(PATH_DATA, "w") as file:
        json.dump(data, file)


def get_data_in_category(link_category):
    start = timeit.default_timer()

    data = read_data_json()

    # GET CATEGORY NAME
    open_link(link_category)
    div_page_title = driver.find_element(By.CLASS_NAME, 'page-title')
    title = div_page_title.find_element(By.TAG_NAME, 'h1').get_attribute('innerText')

    # LOAD JSON CATEGORY BLOCK
    json_category_block = {
        "categoryName": '',
        "recipes": [],
    }

    data.append(json_category_block)

    # SET CATEGORY NAME IN JSON BLOCK
    print("###############################")
    print('Actual Category: ', title)
    print("###############################")
    json_category_block["categoryName"] = title

    # GET RECIPES
    links_element = driver.find_elements(By.XPATH, "//a[contains(@href, '/receita/') and @href != "
                                                   "'/receita/enviar-receita']")
    links = []
    for link in links_element:
        links.append(link.get_attribute('href'))

    for link_recipe in links:
        print(link_recipe)
        # GET INFO'S RECIPE
        try:
            open_link(link_recipe)
        except selenium.common.exceptions.TimeoutException:
            print("Recipe Passed!!!!!!", "TimedPromise timed out after 300000 ms")
        except Exception as e:
            print("Recipe Passed!!!!!!", e)
        else:
            # GET NAME RECIPE
            recipe_name = driver.find_element(By.XPATH, "//div[@class='recipe-title']/h1[1]") \
                .get_attribute('innerText')
            # GET LINK IMAGE
            image_link = driver.find_element(By.XPATH, "//picture[1]/img[1]").get_attribute('src')
            # GET preparationTime
            preparation_time = driver.find_element(By.XPATH, "//time[1]").get_attribute('innerText').replace(" MIN", "")
            # GET yield
            yield_value = driver.find_element(By.XPATH, "//data[@itemprop='recipeYield']").get_attribute("value")
            # JSON RECIPE
            json_recipe_block = {
                "nameRecipe": recipe_name,
                "linkRecipe": link_recipe,
                "linkImage": image_link,
                "ingredients": [],
                "preparation": [],
                "preparationTime": preparation_time,
                "yield": yield_value
            }
            # GET LIST INGREDIENTS
            p_ingredients = driver.find_elements(By.XPATH, "//span[@class='p-ingredient']")

            for p in p_ingredients:
                # p = ingredient element
                ingredient = p.get_attribute('innerText')
                json_recipe_block["ingredients"].append(ingredient)

            # GET LIST PREPARATION
            text_prepatation = driver.find_elements(By.XPATH, "//div[@itemprop='recipeInstructions']/ol/li/span")
            for text in text_prepatation:
                # p = PREPARATION element
                preparation = text.get_attribute('innerText')
                json_recipe_block["preparation"].append(preparation)

            # IF ingredients AND preparation IS EMPTY RETURN LINK UNEXPECTED
            if len(json_recipe_block["ingredients"]) == 0 and len(json_recipe_block["preparation"]) == 0:
                print("ingredients AND preparation IS EMPTY", link_recipe)
            else:
                # json_category_block APPEND json_recipe_block
                json_category_block["recipes"].append(json_recipe_block.copy())

                # ADD DATA JSON (LINKED WITH json_category_block) IN FILE
                write_data_json(data)

    stop = timeit.default_timer()
    print('Category: ' + title + ' Saved in:', str(stop - start) + 's')


def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True


def get_value(ingredient_name):
    search_encode = urllib.parse.quote(ingredient_name)
    url = 'https://www.zonasul.com.br/' + search_encode
    print(url)
    product_value = Decimal('Infinity')
    try:
        request_result = requests.get(url, timeout=(0.3, 27))
        soup = BeautifulSoup(request_result.content, "html.parser")
        script_data_json = soup.find("template", {"data-type": "json", "data-varname": "__STATE__"}).find("script").text
        json_data = json.loads(script_data_json)

        for key in list(json_data.keys()):
            if '.priceRange.listPrice' in key:
                if json_data[key]['highPrice'] < product_value:
                    product_value = json_data[key]['highPrice']
    except Exception as e:
        print('Error for in Request', url, e)

    return float(product_value)


def write_database(recipe, category_name):
    name_recipe = recipe["nameRecipe"]
    print("Saving Recipe", name_recipe, "in DATABASE")
    preparation_mode = '\n'.join(recipe["preparation"])
    recipe_time = recipe["preparationTime"]
    img_path = recipe["linkImage"]

    db.insert_recipe(name_recipe, preparation_mode, recipe_time, img_path)

    db.my_cursor.execute("SELECT LAST_INSERT_ID()")
    id_recipe = db.my_cursor.fetchall()[0][0]

    ignored_words = read_ignored_words()

    for ingredient_info in recipe["ingredients_list"]:
        # INSERT INGREDIENT IN DATABASE
        price = ingredient_info["price"]
        if str(price) == 'inf':
            price = 0

        db.insert_recipe_ingredient(id_recipe, ingredient_info["ingredient"], price)

    db.insert_category(id_recipe, category_name)



def generate_json():
    load_browser()
    data = read_data_json()
    saved_recipes = []

    for row in data:
        saved_recipes.append(row["categoryName"])

    list_categories, list_names = get_categories()
    list_categories_up = []
    for i in range(0, len(list_categories)):
        recipe_name = list_names[i]
        if recipe_name not in saved_recipes:
            list_categories_up.append(list_categories[i])
        else:
            print("Recipe has already been saved:", recipe_name)

    # REMOVE list_categories DATA FROM MEMORY
    list_categories.clear()

    for category in list_categories_up:
        get_data_in_category(category)

    driver.close()

    # LOAD IGNORED WORD
    ignored_words = read_ignored_words()

    print(ignored_words)
    # GET ALL VALUE
    data = read_data_json()

    for index_category, category in enumerate(data):
        print('=============================')
        print('Categorias', index_category, '/', len(data))
        print('=============================')
        for index_recipe, recipe in enumerate(category["recipes"]):
            print('=============================')
            print('Receitas', index_recipe, '/', len(category["recipes"]))
            print('=============================')
            if not 'ingredients_list' in recipe:
                recipe['ingredients_list'] = []

                for ingredient in recipe["ingredients"]:
                    ingredient_filter = ingredient.replace('\xa0', '').split(" ")
                    remove_words = []
    
                    for token in ingredient_filter:

                        for char in token:
                            if char in "0,1,2,3,4,5,6,7,8,9,/":
                                remove_words.append(token)
                        if token in ignored_words:
                            remove_words.append(token)

                    for word in remove_words:
                        try:
                            ingredient_filter.remove(word)
                        except Exception:
                            pass

                    ingredient_cropped = ' '.join(ingredient_filter[0:5])
                    ingredient_cropped.replace('-', ' ')
                    price = get_value(ingredient_cropped)
                    print(ingredient_cropped, price)
                    values = {
                        'ingredient': ingredient,
                        'price': price
                    }
                    recipe['ingredients_list'].append(values)

                del recipe['ingredients']
                print(recipe)
                write_data_json(data)
                write_database(recipe, category["categoryName"])
            else:
                print("Skipping Recipe!")


