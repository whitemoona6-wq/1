import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random

class VocabularyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Тренажер иностранных слов")
        self.root.geometry("800x600")
        
        self.db = VocabularyDatabaseGUI("vocabulary_gui.db")
        self.current_word = None
        self.session_words = []
        self.session_correct = 0
        
        self.setup_ui()
        self.show_main_screen()
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Основной фрейм
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Конфигурация сетки
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        
    def clear_frame(self):
        """Очистка текущего экрана"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    
    def show_main_screen(self):
        """Главный экран"""
        self.clear_frame()
        
        ttk.Label(self.main_frame, text="Тренажер иностранных слов", 
                 font=('Arial', 16, 'bold')).grid(row=0, column=0, columnspan=2, pady=20)
        
        # Кнопки главного меню
        buttons = [
            ("🎓 Учить слова", self.start_study_session),
            ("➕ Добавить слово", self.show_add_word_screen),
            ("📊 Статистика", self.show_statistics_screen),
            ("📈 Прогресс", self.show_progress_screen),
            ("🔍 Поиск слов", self.show_search_screen)
        ]
        
        for i, (text, command) in enumerate(buttons):
            ttk.Button(self.main_frame, text=text, command=command,
                      width=20).grid(row=i+1, column=0, columnspan=2, pady=5)
    
    def start_study_session(self):
        """Начало сессии изучения"""
        self.session_words = self.db.get_words_for_review(10)
        if not self.session_words:
            messagebox.showinfo("Информация", "Нет слов для повторения! Добавьте новые слова.")
            return
        
        self.session_correct = 0
        self.current_word_index = 0
        self.show_study_screen()
    
    def show_study_screen(self):
        """Экран изучения слов"""
        self.clear_frame()
        
        if self.current_word_index >= len(self.session_words):
            self.finish_session()
            return
        
        self.current_word = self.session_words[self.current_word_index]
        word_id, original, translation, lang, diff, correct, total, last_rev, next_rev, created = self.current_word
        
        # Прогресс сессии
        progress = (self.current_word_index / len(self.session_words)) * 100
        ttk.Label(self.main_frame, text=f"Прогресс: {self.current_word_index + 1}/{len(self.session_words)}").grid(row=0, column=0, sticky=tk.W)
        
        # Отображение слова
        ttk.Label(self.main_frame, text=original, font=('Arial', 24, 'bold')).grid(row=1, column=0, columnspan=2, pady=30)
        ttk.Label(self.main_frame, text=f"Сложность: {'★' * diff}").grid(row=2, column=0, columnspan=2)
        
        # Поле для ввода перевода
        ttk.Label(self.main_frame, text="Введите перевод:").grid(row=3, column=0, sticky=tk.W, pady=10)
        self.answer_var = tk.StringVar()
        answer_entry = ttk.Entry(self.main_frame, textvariable=self.answer_var, width=30, font=('Arial', 12))
        answer_entry.grid(row=3, column=1, pady=10, padx=10)
        answer_entry.bind('<Return>', lambda e: self.check_answer())
        
        # Кнопки
        ttk.Button(self.main_frame, text="Проверить", command=self.check_answer).grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(self.main_frame, text="Пропустить", command=self.skip_word).grid(row=5, column=0, columnspan=2)
        
        answer_entry.focus()
    
    def check_answer(self):
        """Проверка ответа"""
        user_answer = self.answer_var.get().strip().lower()
        word_id, original, translation, lang, diff, correct, total, last_rev, next_rev, created = self.current_word
        
        if user_answer == translation.lower():
            self.db.update_word_stats(word_id, True)
            self.session_correct += 1
            messagebox.showinfo("Результат", "✓ Правильно!")
        else:
            self.db.update_word_stats(word_id, False)
            messagebox.showinfo("Результат", f"✗ Неправильно!\nПравильный ответ: {translation}")
        
        self.current_word_index += 1
        self.show_study_screen()
    
    def skip_word(self):
        """Пропуск слова"""
        self.current_word_index += 1
        self.show_study_screen()
    
    def finish_session(self):
        """Завершение сессии"""
        success_rate = (self.session_correct / len(self.session_words)) * 100
        self.db.save_session_stats(len(self.session_words), self.session_correct)
        
        messagebox.showinfo(
            "Сессия завершена", 
            f"Результат: {self.session_correct}/{len(self.session_words)}\nУспешность: {success_rate:.1f}%"
        )
        
        self.show_main_screen()
    
    def show_add_word_screen(self):
        """Экран добавления нового слова"""
        self.clear_frame()
        
        ttk.Label(self.main_frame, text="Добавление нового слова", font=('Arial', 14, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Поля ввода
        ttk.Label(self.main_frame, text="Иностранное слово:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.word_var = tk.StringVar()
        ttk.Entry(self.main_frame, textvariable=self.word_var, width=30).grid(row=1, column=1, pady=5, padx=10)
        
        ttk.Label(self.main_frame, text="Перевод:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.translation_var = tk.StringVar()
        ttk.Entry(self.main_frame, textvariable=self.translation_var, width=30).grid(row=2, column=1, pady=5, padx=10)
        
        ttk.Label(self.main_frame, text="Язык:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.language_var = tk.StringVar(value="english")
        ttk.Entry(self.main_frame, textvariable=self.language_var, width=30).grid(row=3, column=1, pady=5, padx=10)
        
        ttk.Label(self.main_frame, text="Сложность:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.difficulty_var = tk.IntVar(value=1)
        ttk.Combobox(self.main_frame, textvariable=self.difficulty_var, 
                    values=[1, 2, 3], state="readonly", width=27).grid(row=4, column=1, pady=5, padx=10)
        
        # Кнопки
        ttk.Button(self.main_frame, text="Добавить", command=self.add_word).grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Button(self.main_frame, text="Назад", command=self.show_main_screen).grid(row=6, column=0, columnspan=2)
    
    def add_word(self):
        """Добавление слова в базу данных"""
        word = self.word_var.get().strip()
        translation = self.translation_var.get().strip()
        language = self.language_var.get().strip()
        difficulty = self.difficulty_var.get()
        
        if not word or not translation:
            messagebox.showerror("Ошибка", "Заполните все поля!")
            return
        
        self.db.add_word(word, translation, language, difficulty)
        messagebox.showinfo("Успех", f"Слово '{word}' добавлено!")
        self.show_main_screen()
    
    def show_statistics_screen(self):
        """Экран статистики"""
        self.clear_frame()
        
        ttk.Label(self.main_frame, text="Статистика", font=('Arial', 14, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)
        
        stats = self.db.get_statistics()
        
        # Основная статистика
        stats_text = f"""
        Всего слов: {stats['total_words']}
        Изученных слов: {stats['mastered_words']}
        Успешность: {stats['success_rate']}%
        Слов для повторения: {stats['due_for_review']}
        """
        
        ttk.Label(self.main_frame, text=stats_text, justify=tk.LEFT).grid(row=1, column=0, columnspan=2, pady=10)
        
        # Таблица слов
        columns = ("ID", "Слово", "Перевод", "Сложность", "Успешность")
        tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        # Получаем все слова для отображения
        words = self.db.get_all_words()
        for word in words:
            word_id, original, translation, lang, diff, correct, total, last_rev, next_rev, created = word
            success_rate = (correct / total * 100) if total > 0 else 0
            tree.insert("", "end", values=(
                word_id, original, translation, "★" * diff, f"{success_rate:.1f}%"
            ))
        
        tree.grid(row=2, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        # Кнопка назад
        ttk.Button(self.main_frame, text="Назад", command=self.show_main_screen).grid(row=3, column=0, columnspan=2, pady=10)
    
    def show_progress_screen(self):
        """Экран прогресса с графиками"""
        self.clear_frame()
        
        ttk.Label(self.main_frame, text="Прогресс изучения", font=('Arial', 14, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Создаем график
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
        
        # График 1: Статистика успешности по словам
        words_stats = self.db.get_words_success_stats()
        if words_stats:
            words, success_rates = zip(*words_stats)
            ax1.bar(words, success_rates)
            ax1.set_title("Успешность по словам")
            ax1.set_xticklabels(words, rotation=45, ha='right')
        
        # График 2: Прогресс по сессиям
        session_stats = self.db.get_session_stats()
        if session_stats:
            dates, success_rates = zip(*session_stats)
            ax2.plot(dates, success_rates, marker='o')
            ax2.set_title("Прогресс по сессиям")
            ax2.set_xticklabels(dates, rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Встраиваем график в Tkinter
        canvas = FigureCanvasTkAgg(fig, self.main_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(self.main_frame, text="Назад", command=self.show_main_screen).grid(row=2, column=0, columnspan=2, pady=10)
    
    def show_search_screen(self):
        """Экран поиска слов"""
        self.clear_frame()
        
        ttk.Label(self.main_frame, text="Поиск слов", font=('Arial', 14, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)
        
        ttk.Label(self.main_frame, text="Поиск:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(self.main_frame, textvariable=self.search_var, width=30)
        search_entry.grid(row=1, column=1, pady=5, padx=10)
        search_entry.bind('<KeyRelease>', self.perform_search)
        
        # Таблица результатов
        columns = ("Слово", "Перевод", "Язык", "Сложность")
        self.search_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.search_tree.heading(col, text=col)
            self.search_tree.column(col, width=150)
        
        self.search_tree.grid(row=2, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Button(self.main_frame, text="Назад", command=self.show_main_screen).grid(row=3, column=0, columnspan=2, pady=10)
    
    def perform_search(self, event=None):
        """Выполнение поиска"""
        query = self.search_var.get().strip().lower()
        
        # Очищаем предыдущие результаты
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)
        
        if not query:
            return
        
        # Поиск по словам и переводам
        words = self.db.search_words(query)
        for word in words:
            word_id, original, translation, lang, diff, correct, total, last_rev, next_rev, created = word
            self.search_tree.insert("", "end", values=(
                original, translation, lang, "★" * diff
            ))

class VocabularyDatabaseGUI(VocabularyDatabase):
    def __init__(self, db_name="vocabulary_gui.db"):
        super().__init__(db_name)
    
    def get_all_words(self):
        """Получение всех слов"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM words ORDER BY word')
        words = cursor.fetchall()
        conn.close()
        return words
    
    def search_words(self, query):
        """Поиск слов"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM words 
            WHERE LOWER(word) LIKE ? OR LOWER(translation) LIKE ?
            ORDER BY word
        ''', (f'%{query}%', f'%{query}%'))
        words = cursor.fetchall()
        conn.close()
        return words
    
    def get_words_success_stats(self):
        """Статистика успешности по словам"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT word, 
                   CASE WHEN total_attempts > 0 THEN (correct_answers * 100.0 / total_attempts) 
                        ELSE 0 END as success_rate
            FROM words 
            WHERE total_attempts > 0
            ORDER BY success_rate DESC
            LIMIT 10
        ''')
        stats = cursor.fetchall()
        conn.close()
        
        # Ограничиваем длину названий слов для графика
        formatted_stats = []
        for word, rate in stats:
            short_word = word[:10] + '...' if len(word) > 10 else word
            formatted_stats.append((short_word, rate))
        
        return formatted_stats
    
    def get_session_stats(self):
        """Статистика по сессиям"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT session_date, 
                   (correct_answers * 100.0 / NULLIF(words_studied, 0)) as success_rate
            FROM study_sessions 
            WHERE words_studied > 0
            ORDER BY session_date
            LIMIT 10
        ''')
        stats = cursor.fetchall()
        conn.close()
        
        # Форматируем даты
        formatted_stats = []
        for date, rate in stats:
            short_date = str(date)[5:]  # Берем только месяц и день
            formatted_stats.append((short_date, rate or 0))
        
        return formatted_stats
    
    def get_statistics(self):
        """Расширенная статистика"""
        stats = super().get_statistics()
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM words WHERE next_review <= ?', (datetime.now().date(),))
        stats['due_for_review'] = cursor.fetchone()[0]
        
        conn.close()
        return stats

if __name__ == "__main__":
    root = tk.Tk()
    app = VocabularyApp(root)
    root.mainloop()