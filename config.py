from sshtunnel import SSHTunnelForwarder
import psycopg2 as pg

TOKEN = '2027170032:AAH-g30BipQVW7IwY_lao48A1RfjRomb4uY'
SECRET_PIN = '444078AADCAF6696'
API_KEY = '19af-fa32-c73b-01ac'
version = 2


async def db_exec(string):
    with SSHTunnelForwarder(
            ('188.32.33.13', 2442),
            ssh_username="chel",
            ssh_password="FGF6y6u7",
            remote_bind_address=('127.0.0.1', 5432)) as server:
        server.start()
        params = {
            'database': 'postgres',
            'user': 'postgres',
            'password': '1234',
            'host': 'localhost',
            'port': server.local_bind_port
        }

        conn = pg.connect(**params)
        curs = conn.cursor()
        curs.execute(string)
        rows = curs.fetchall()
        return rows
