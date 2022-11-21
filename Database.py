import mysql.connector

mydb = mysql.connector.connect(
    host="localhost",
    database="bddicadavovo2",
    user="root",
    password=""
)

my_cursor = mydb.cursor()


def insert_recipe(name_recipe, preparation_mode, recipe_time, img_path):
    sql = "INSERT INTO `tbreceita`(`nomeReceita`, `modoPreparo`, `tempoReceita`, `caminhoImg`) VALUES (%s, %s, %s, %s)"
    val = (name_recipe, preparation_mode, recipe_time, img_path)
    my_cursor.execute(sql, val)

    mydb.commit()


def insert_category(id_recipe, category_name):
    sql = "INSERT INTO `tbcategoria`(`idReceita`, `descCategoria`) VALUES (%s, %s)"
    val = (id_recipe, category_name)
    my_cursor.execute(sql, val)

    mydb.commit()


def insert_recipe_ingredient(id_recipe, name_ingredient, price_ingredient):
    sql = "CALL cadastrar_receitaIngrediente(%s, %s, %s)"
    val = (id_recipe, name_ingredient, price_ingredient)
    my_cursor.execute(sql, val)

    mydb.commit()
