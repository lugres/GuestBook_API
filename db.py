from psycopg2 import connect, sql
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from os import environ as env

load_dotenv()


class Database:
    '''A more generic DB helper'''

    def __init__(self):
        # initializing attributes
        self.conn = None
        self.cursor = None

    def open(self, url=None):
        """Opening a connection to DB"""
        if not url:
            url = env.get('CONNECTION_URL')
        self.conn = connect(url)
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)

    def close(self):
        self.cursor.close()
        self.conn.close()

    @staticmethod
    def _compose_kv_and(separator=' AND ', joiner=' = ', kv_pairs=None):

        return sql.SQL(separator).join(
            sql.SQL("{}" + joiner + "{}").format(
                sql.Identifier(k), sql.Literal(v)) for k, v in kv_pairs
        )

    def get(self, table: str, columns: list[str], limit: int = None, where: dict = None, or_where: dict = None, contains: dict = None):
        '''Getting specified number of rows from a table for specified columns with optional WHERE, OR_WHERE and CONTAINS'''

        composed_query = sql.SQL("select {} from {}").format(
            sql.SQL(',').join(map(sql.Identifier, columns)),
            sql.Identifier(table)
        )

        if contains:
            transformed_contains = {
                k: f"%{v}%" for (k, v) in contains.items()}

            composed_query += sql.SQL(" where {}").format(
                self._compose_kv_and(separator=' or ', joiner=' like ', kv_pairs=transformed_contains.items()))

        if where:
            starter = sql.SQL(" where ({})")

            if contains:
                if or_where:
                    starter = sql.SQL(" and (({})")
                else:
                    starter = sql.SQL(" and ({})")

            composed_query += starter.format(
                self._compose_kv_and(kv_pairs=where.items())
            )

        if where and or_where:
            composed_query += sql.SQL(" or ({})").format(
                self._compose_kv_and(kv_pairs=or_where.items()))

            if contains:
                composed_query += sql.SQL(")")

        if limit:
            composed_query += sql.SQL(' limit {}').format(sql.Literal(limit))

        # composed_query = sql.SQL("select {} from {}").format(
        #     sql.SQL(',').join(map(sql.Identifier, columns)),
        #     sql.Identifier(table)
        # )

        # if where:
        #     composed_query += sql.SQL(" where {}").format(
        #         self._compose_kv_and(kv_pairs=where.items())
        #         # sql.SQL(" and ").join(
        #         #     map(lambda x: sql.SQL("{} = {}").format(
        #         #         sql.Identifier(x), sql.Literal(where.get(x))
        #         #     ), where)
        #         # )
        #     )

        # if where and or_where:
        #     composed_query += sql.SQL(" or ({})").format(
        #         self._compose_kv_and(kv_pairs=or_where.items())
        #         # sql.SQL(' and ').join(
        #         #     sql.SQL("{} = {}").format(
        #         #         sql.Identifier(k), sql.Literal(v)
        #         #     ) for k, v in or_where.items()
        #         # )
        #     )

        # if contains:
        #     transformed_contains = {
        #         k: f"%{v}%" for (k, v) in contains.items()}
        #     if where:
        #         # joining with AND
        #         composed_query += sql.SQL(" and {}").format(
        #             self._compose_kv_and(separator=' or ', joiner='like', kv_pairs=transformed_contains.items()))
        #     else:
        #         # joining with WHERE
        #         composed_query += sql.SQL(" where {}").format(
        #             self._compose_kv_and(separator=' or ', joiner='like', kv_pairs=transformed_contains.items()))

        # if limit:
        #     composed_query += sql.SQL(' limit {}').format(sql.Literal(limit))

        print(composed_query.as_string(self.conn))

        self.cursor.execute(composed_query)
        return self.cursor.fetchall()

    def get_one(self, table: str, columns: list[str], where: dict = None):
        '''Getting a single row in a form of dict from a table for specified columns with optional WHERE'''
        result = self.get(table, columns, limit=1, where=where)  # [{}]
        if len(result):
            return result[0]  # {}

    def get_contains(self, table: str, columns: list[str], search: str, limit: int = None):
        '''Getting records where a search term is present in specified columns'''

        # ... WHERE col1 LIKE %search% OR col2 LIKE %search%
        composed_query = sql.SQL("select {} from {} where {}").format(
            sql.SQL(',').join(map(sql.Identifier, columns)),
            sql.Identifier(table),
            sql.SQL(' or ').join(
                sql.SQL('{} like {}').format(
                    sql.Identifier(k), sql.Literal(f"%{search}%")) for k in columns
            )
        )

        if limit:
            composed_query += sql.SQL(' limit {}').format(sql.Literal(limit))

        self.cursor.execute(composed_query)
        return self.cursor.fetchall()

    def write(self, table: str, columns: list[str], values: list):
        '''Writing into a table an arbitrary number of values'''

        composed_query = sql.SQL("""
            insert into {} ({})
            values ({}) returning id;
        """).format(
            sql.Identifier(table),
            sql.SQL(',').join(map(sql.Identifier, columns)),
            sql.SQL(',').join(map(sql.Literal, values))
        )

        self.cursor.execute(composed_query)
        self.conn.commit()
        return self.cursor.fetchone().get('id')

    def update(self, table: str, columns: list[str], values: list, where: dict = None):
        '''Updating an arbitrary number of columns with values, with optional WHERE.
            Returning a number of affected rows.
        '''

        # using a generator of tuples (mapping is possible as an alternative)
        # set_clause = sql.SQL(' , ').join(
        #     sql.SQL(' {} = {} ').format(
        #         sql.Identifier(column), sql.Literal(value)) for column, value in zip(columns, values)
        # )
        set_clause = self._compose_kv_and(
            separator=',', kv_pairs=zip(columns, values))

        query = sql.SQL("""
            update {}
            set {}            
        """).format(sql.Identifier(table), set_clause)

        # using a mapping function (a generator is possible instead with .items(), see above)
        # we could have re-factored this out and use across other methods (get, update, etc)
        if where:
            query += sql.SQL(' where {}').format(
                self._compose_kv_and(kv_pairs=where.items())
                #     sql.SQL(' and ').join(
                #     map(lambda x: sql.SQL('{} = {}').format(
                #         sql.Identifier(x), sql.Literal(where.get(x))), where)
                # )
            )

        # return query
        self.cursor.execute(query)
        self.conn.commit()
        return self.cursor.rowcount

    def delete(self, table: str, where: dict = None):

        composed_query = sql.SQL("delete from {}").format(
            sql.Identifier(table)
        )

        if where:
            composed_query += sql.SQL(" where {}").format(
                self._compose_kv_and(kv_pairs=where.items())
                # sql.SQL(' and ').join(
                #     sql.SQL("{} = {}").format(
                #         sql.Identifier(k), sql.Literal(v)
                #     ) for k, v in where.items()
                # )
            )

        self.cursor.execute(composed_query)
        self.conn.commit()
        return self.cursor.rowcount
