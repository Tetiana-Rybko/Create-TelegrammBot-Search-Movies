class FilmSearch:
    def __init__(self, db_manager):
        self.db = db_manager

    def search_by_keyword(self, keyword):
        # Ищем фильмы по ключевому слову в названии
        sql = "SELECT title, release_year FROM film WHERE title LIKE %s LIMIT 10"
        like_keyword = f"%{keyword}%"
        results = self.db.execute_query(sql, (like_keyword,))
        return results

    def search_by_genre_and_year(self, genre, year):

        sql = """
            SELECT f.title, c.name AS category, f.release_year 
            FROM film f
            JOIN film_category fc ON f.film_id = fc.film_id
            JOIN category c ON fc.category_id = c.category_id
            WHERE c.name = %s AND f.release_year = %s
            LIMIT 10
        """
        results = self.db.execute_query(sql, (genre, year))
        return results