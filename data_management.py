#!/usr/local/bin/python3
# coding: utf8

import records
from download import DataToMySql, CsvAnalysis


class Data:

    def __init__(self):
        _connect = 'mysql+mysqldb://root:MyNewPass@localhost/OpenFoodFacts'
        self._db = records.Database(_connect)

        # Check if the databse is not empty
        data = self._db.query('SELECT id_product FROM products LIMIT 1')
        # If the database is empty, load the database
        if data.first() is None:
            success = self.update_database()
            if success is False:
                print("Une erreur s'est produite avec la base de donnée")

    def select_categories(self):
        sql = 'SELECT category_name FROM categories '
        categories = self._db.query(sql)
        categories_list = self.list_items(categories)
        return categories_list

    def select_subcategories(self, cat, page=1, nb_element=10):
        f_element = (nb_element * (page - 1))
        query = 'SELECT id_subcategory, subcategory_name '
        query += 'FROM subcategories AS s '
        query += 'INNER JOIN categories AS c '
        query += 'ON s.name_category = c.category_name '
        query += 'WHERE category_name = "%s" LIMIT %i OFFSET %i'
        subcategories = self._db.query(query % (cat, nb_element, f_element))
        subcategories_list = self.list_items(subcategories)
        id_sub = []
        sub_name = []
        for value in subcategories:
            id_sub.append(value.id_subcategory)
            sub_name.append(value.subcategory_name)
        return id_sub, sub_name

    def select_products(self, id_sub, page=1, nb_element=10):
        f_element = (nb_element * (page - 1))
        query = 'SELECT id_product, product_name from products AS p '
        query += 'INNER JOIN subcategories AS s '
        query += 'ON p.subcategory_id= s.id_subcategory '
        query += 'WHERE id_subcategory = %i '
        query += 'AND product_replacement_id is NULL '
        query += 'LIMIT %i OFFSET %i'
        products = self._db.query(query % (id_sub, nb_element, f_element))
        id_prod = []
        product_name = []
        for value in products:
            id_prod.append(value.id_product)
            product_name.append(value.product_name)
        return id_prod, product_name

    def select_substitutes(self, id_sub, id_prod,  page=1, nb_element=10):
        f_element = (nb_element * (page - 1))
        sql = 'SELECT id_product, product_name, brand, url_text '
        sql += 'FROM products AS p '
        sql += 'INNER JOIN subcategories AS s '
        sql += 'ON s.id_subcategory=p.subcategory_id '
        sql += 'WHERE id_subcategory = %i AND id_product != %i '
        sql += 'ORDER BY nutrition_score'
        sql += ' ASC LIMIT %i OFFSET %i'
        substitutes = self._db.query(sql % (id_sub, id_prod, nb_element, f_element))
        id_subs = []
        for value in substitutes:
            id_subs.append(value.id_product)
        return id_subs, substitutes

    def select_product_and_substitute(self, page=1, nb_element=10):
        f_element = (nb_element * (page - 1))
        sql = 'SELECT product_id, product_name '
        sql += 'FROM products as p '
        sql += 'INNER JOIN replacement_products as r '
        sql += 'ON p.product_replacement_id = r.id_product_replacement '
        sql += 'ORDER BY added_date DESC '
        sql += 'LIMIT %i OFFSET %i'
        products_substitutes = self._db.query(sql % (nb_element, f_element))

        prod_sub = ()
        products_and_substitutes = []
        for val in products_substitutes:
            repl_product = self.replacement_prod_name(val.product_id)
            product_replaced = val.product_name
            prod_sub = (repl_product[0].product_name , product_replaced)
            products_and_substitutes.append(prod_sub)

        return products_and_substitutes

    def replacement_prod_name(self, prod_id):
        sql = 'SELECT product_name '
        sql += 'FROM products AS p '
        sql += 'WHERE id_product = %i '
        return self._db.query(sql % prod_id)

    def select_information_products(self, id_prod):
        sql = 'SELECT product_name, quantity, packaging, origin, allergens,  '
        sql += 'traces, additives_number, additives '
        sql += 'FROM products '
        sql += 'WHERE id_product = %i'
        info = self._db.query(sql % (id_prod))
        return info

    def list_items(self, items):
        cat = []
        for value in items:
            cat.append(value[0])
        return cat

    def add_substitute(self, product_id, replacement_prod_id):
        # Check if the substitute is not already in the table
        sql = 'SELECT product_id FROM Replacement_products '
        sql += 'WHERE product_id = %i'
        sub_known = self._db.query(sql % (replacement_prod_id))
        if sub_known != " ":
            insert = "INSERT INTO Replacement_products"
            insert += '(product_id) VALUES (%i)'
            self._db.query(insert % (replacement_prod_id))

        update = 'UPDATE Products SET product_replacement_id = '
        update += '(SELECT id_product_replacement FROM replacement_products '
        update += 'WHERE product_id = %i), added_date = NOW() '
        update += 'WHERE id_product = %i'
        self._db.query(update % (replacement_prod_id, product_id))

    def update_database(self):
        db = DataToMySql()
        csv = CsvAnalysis()
        csv.download_file()
        # Remove all the data in the database
        self._db.query('DELETE FROM subcategories')
        self._db.query('DELETE FROM categories')
        self._db.query('DELETE FROM products')
        self._db.query('DELETE FROM replacement_products')
        # Insert new value from internet
        return db.insert_into_db()


class UserChoice:

    def __init__(self):
        self._dt = Data()
        self._chosen_category = ""
        self._chosen_subcategory = 0
        self._chosen_product = 0
        self._chosen_substitute = 0

    @property
    def chosen_category(self):
        return self._chosen_category

    @property
    def chosen_subcategory(self):
        return self._chosen_subcategory

    @chosen_subcategory.setter
    def chosen_subcategory(self, value):
        self._chosen_subcategory = value

    @property
    def chosen_product(self):
        return self._chosen_product

    @chosen_product.setter
    def chosen_product(self, value):
        self._chosen_product = value

    @property
    def chosen_substitute(self):
        return self._chosen_substitute

    @chosen_substitute.setter
    def chosen_substitute(self, value):
        self._chosen_substitute = value

    def choose_category(self, number, *cat):
        for key, value in enumerate(*cat):
            if key == number:
                self._chosen_category = value
                break