import sqlite3
import random
from datetime import datetime, timedelta

class VocabularyDatabase:
    def __init__(self, db_name="vocabulary.db"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Таблица слов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                translation TEXT NOT NULL,
                language TEXT DEFAULT 'english',
                difficulty INTEGER DEFAULT 1,
                correct_answers INTEGER DEFAULT 0,
                total_attempts INTEGER DEFAULT 0,
                last_reviewed DATE,
                next_review DATE,
                created_date DATE DEFAULT CURRENT_DATE
            )
        ''')
        
        # Таблица сессий изучения
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_date DATE DEFAULT CURRENT_DATE,
                words_studied INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0,
                session_duration INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_word(self, word, translation, language="english", difficulty=1):
        """Добавление нового слова"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO words (word, translation, language, difficulty, last_reviewed, next_review)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (word, translation, language, difficulty, datetime.now().date(), datetime.now().date()))
        
        conn.commit()
        conn.close()
    
    def get_words_for_review(self, limit=10):
        """Получение слов для повторения"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM words 
            WHERE next_review <= ? OR next_review IS NULL
            ORDER BY difficulty DESC, correct_answers ASC
            LIMIT ?
        ''', (datetime.now().date(), limit))
        
        words = cursor.fetchall()
        conn.close()
        return words
    
    def update_word_stats(self, word_id, is_correct):
        """Обновление статистики слова"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Получаем текущие данные
        cursor.execute('SELECT correct_answers, total_attempts, difficulty FROM words WHERE id = ?', (word_id,))
        result = cursor.fetchone()
        
        if result:
            correct_answers, total_attempts, difficulty = result
            
            # Обновляем статистику
            new_correct = correct_answers + 1 if is_correct else correct_answers
            new_total = total_attempts + 1
            
            # Рассчитываем следующую дату повторения (алгоритм интервального повторения)
            if is_correct:
                # Увеличиваем интервал в зависимости от правильных ответов
                interval_days = min(30, 2 ** (new_correct // 3))
                next_review = datetime.now().date() + timedelta(days=interval_days)
            else:
                # Если ошибся - повторяем завтра
                next_review = datetime.now().date() + timedelta(days=1)
            
            cursor.execute('''
                UPDATE words 
                SET correct_answers = ?, total_attempts = ?, 
                    last_reviewed = ?, next_review = ?
                WHERE id = ?
            ''', (new_correct, new_total, datetime.now().date(), next_review, word_id))
        
        conn.commit()
        conn.close()
    
    def get_statistics(self):
        """Получение общей статистики"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM words')
        total_words = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM words WHERE correct_answers >= 5')
        mastered_words = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(correct_answers * 100.0 / NULLIF(total_attempts, 0)) FROM words WHERE total_attempts > 0')
        avg_success = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_words': total_words,
            'mastered_words': mastered_words,
            'success_rate': round(avg_success, 1)
        }

class VocabularyTrainer:
    def __init__(self):
        self.db = VocabularyDatabase()
        self.add_sample_data()
    
    def add_sample_data(self):
        """Добавление примеров слов для демонстрации"""
        sample_words = [
            ("hello", "привет", "english", 1),
            ("goodbye", "до свидания", "english", 1),
            ("computer", "компьютер", "english", 2),
            ("beautiful", "красивый", "english", 3),
            ("knowledge", "знание", "english", 3),
            ("apple", "яблоко", "english", 1),
            ("house", "дом", "english", 1),
            ("book", "книга", "english", 1),
        ]
        
        # Проверяем, есть ли уже слова в базе
        stats = self.db.get_statistics()
        if stats['total_words'] == 0:
            for word, translation, lang, diff in sample_words:
                self.db.add_word(word, translation, lang, diff)
            print("Добавлены демонстрационные слова!")
    
    def study_session(self):
        """Сессия изучения слов"""
        words = self.db.get_words_for_review(5)
        
        if not words:
            print("Нет слов для повторения! Добавьте новые слова.")
            return
        
        print(f"\n=== Сессия изучения ({len(words)} слов) ===")
        correct_count = 0
        
        for word in words:
            word_id, original, translation, lang, diff, correct, total, last_rev, next_rev, created = word
            
            print(f"\nСлово: {original} (Сложность: {diff}/3)")
            user_translation = input("Перевод: ").strip().lower()
            
            if user_translation == translation.lower():
                print("✓ Правильно!")
                self.db.update_word_stats(word_id, True)
                correct_count += 1
            else:
                print(f"✗ Неправильно. Правильный ответ: {translation}")
                self.db.update_word_stats(word_id, False)
        
        success_rate = (correct_count / len(words)) * 100
        print(f"\nРезультат: {correct_count}/{len(words)} ({success_rate:.1f}%)")
        
        # Сохраняем статистику сессии
        self.save_session_stats(len(words), correct_count)
    
    def save_session_stats(self, words_studied, correct_answers):
        """Сохранение статистики сессии"""
        conn = sqlite3.connect(self.db.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO study_sessions (words_studied, correct_answers)
            VALUES (?, ?)
        ''', (words_studied, correct_answers))
        
        conn.commit()
        conn.close()
    
    def add_new_word(self):
        """Добавление нового слова"""
        print("\n=== Добавление нового слова ===")
        word = input("Иностранное слово: ").strip()
        translation = input("Перевод: ").strip()
        language = input("Язык (по умолчанию english): ").strip() or "english"
        
        try:
            difficulty = int(input("Сложность (1-3, по умолчанию 1): ").strip() or "1")
            difficulty = max(1, min(3, difficulty))  # Ограничение 1-3
        except ValueError:
            difficulty = 1
        
        self.db.add_word(word, translation, language, difficulty)
        print(f"Слово '{word}' добавлено!")
    
    def show_statistics(self):
        """Показать статистику"""
        stats = self.db.get_statistics()
        print("\n=== Статистика ===")
        print(f"Всего слов: {stats['total_words']}")
        print(f"Изученных слов: {stats['mastered_words']}")
        print(f"Успешность: {stats['success_rate']}%")
    
    def run(self):
        """Основной цикл программы"""
        while True:
            print("\n=== Тренажер иностранных слов ===")
            print("1. Учить слова")
            print("2. Добавить слово")
            print("3. Статистика")
            print("4. Выход")
            
            choice = input("Выберите действие: ").strip()
            
            if choice == "1":
                self.study_session()
            elif choice == "2":
                self.add_new_word()
            elif choice == "3":
                self.show_statistics()
            elif choice == "4":
                print("До свидания!")
                break
            else:
                print("Неверный выбор!")

if __name__ == "__main__":
    trainer = VocabularyTrainer()
    trainer.run()