import pymysql.cursors


class DatabaseManager:
    def __init__(self,host,user,password,database):
        try:
           self.connection = pymysql.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                cursorclass=pymysql.cursors.DictCursor
            )
           self.cursor = self.connection.cursor()
           print("Подключение к базе!" )
           print("Добро пожаловать в бота для поиска фильмов!")
        except pymysql.MySQLError as e:
            print("Ошибка подключения",e)
            raise
    def execute_query(self, query, params=None):
        self.cursor.execute(query, params or ())
        return self.cursor.fetchall()
    def close(self):
        self.cursor.close()
        self.connection.close()