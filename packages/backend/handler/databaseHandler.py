import sqlite3

class CalendarDatabase:
    createTableStatements = [
        """CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                name TEXT,
                startDate INTEGER,
                duration INTEGER,
                frequencyRuleId TEXT,
                conditionRuleId TEXT,
                timeRemaining INTEGER,
                iterationsRemaining INTEGER,
                deadline INTEGER,
                allowesTags TEXT,
                tags TEXT,
        
                FOREIGN KEY(frequencyRuleId) REFERENCES frequencyRules(id),
                FOREIGN KEY(conditionRuleId) REFERENCES conditionRules(id)
            );""",

        """CREATE TABLE IF NOT EXISTS frequencyRules (
                id TEXT PRIMARY KEY,
                unit TEXT,
                rate REAL
            );""",

        """CREATE TABLE IF NOT EXISTS conditionRules (
                id TEXT PRIMARY KEY,
                reference TEXT,
                referenceFactor REAL,
                unit TEXT,
                unitFactor REAL,
                number INTEGER
            );"""
    ]
        
    
    def __init__(self) -> None:
        with sqlite3.connect("abcDatabase.db") as database:
            cursor = database.cursor()

            for table in self.createTableStatements:
                cursor.execute(table)

            database.commit()
            print('Tables created successfully')

if __name__ == '__main__':
    calendar = CalendarDatabase()


