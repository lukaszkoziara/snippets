import sqlite3


def main():
    conn = sqlite3.connect('/path/to/file.db')
    cur = conn.cursor()

    for row in [elem for elem in cur.execute('SELECT * FROM download WHERE finished = ?', ('false', ))]:
        chunk_name = row[0]
        if 'binaries' in chunk_name:
            cur.execute('UPDATE download SET finished = ? WHERE filename = ?', ('true', chunk_name,))
            conn.commit()

    conn.close()


if __name__ == 'main':
    main()
