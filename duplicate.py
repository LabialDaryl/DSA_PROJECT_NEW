import sqlite3
import sys

import requests
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QMovie
from PyQt5.QtWidgets import QMessageBox, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidgetItem, \
    QPushButton, QLabel, QLineEdit, QApplication, QListWidget, QStackedLayout, QSpacerItem, QSizePolicy, QDialog, \
    QTableWidgetItem, QAction, QMenu, QTableWidget, QHeaderView

DB_FILE = "app_database.db"  # SQLite database file


def toggle_password_visibility(password_input, button):
    """Toggles the visibility of the password."""
    if password_input.echoMode() == QLineEdit.Password:
        password_input.setEchoMode(QLineEdit.Normal)
        button.setIcon(QIcon("assets/view.png"))  # Use an icon for "eye closed"
    else:
        password_input.setEchoMode(QLineEdit.Password)
        button.setIcon(QIcon("assets/hide.png"))  # Use an icon for "eye open"


class Auth(QMainWindow):
    def __init__(self):
        super().__init__()
        self.loading_dialog = None
        self.main_app = None
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setFixedSize(700, 500)
        self.setStyleSheet("background-color: #6BA3BE;")
        self.center_window()


        # Central widget and layout
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        # Header layout (for the close button)
        header_layout = QHBoxLayout()
        header_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Custom close button
        close_button = QPushButton("X")
        close_button.setFixedSize(30, 30)
        close_button.setFont(QFont("Arial", 10, QFont.Bold))
        close_button.setStyleSheet("""
            QPushButton {
                background-color: darkred;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: black;
            }
        """)
        close_button.clicked.connect(self.close)
        header_layout.addWidget(close_button)
        layout.addLayout(header_layout)

        # App Title
        title = QLabel("Book Library")
        title.setFont(QFont("Arial", 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #031716;")
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Read with Passion.")
        subtitle.setFont(QFont("Brush Script MT", 30))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #0000;")
        layout.addWidget(subtitle)


        layout.addSpacing(20)  # Spacer

        # Username input
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setFont(QFont("Arial", 14))
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: #fff;
            }
            QLineEdit:focus {
                border: 2px solid #4267B2;
            }
        """)
        layout.addWidget(self.username_input)

        # Password input layout
        password_layout = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFont(QFont("Arial", 14))
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: #fff;
            }
            QLineEdit:focus {
                border: 2px solid #4267B2;
            }
        """)
        password_layout.addWidget(self.password_input)

        # Toggle password visibility button
        self.toggle_button = QPushButton()
        self.toggle_button.setIcon(QIcon("assets/hide.png"))  # Update path if necessary
        self.toggle_button.setStyleSheet("border: none;")
        self.toggle_button.setFixedSize(40, 40)
        self.toggle_button.clicked.connect(lambda: toggle_password_visibility(self.password_input, self.toggle_button))
        password_layout.addWidget(self.toggle_button)
        layout.addLayout(password_layout)

        # Login Button
        self.login_button = QPushButton("Log In")
        self.login_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #4267B2;
                color: white;
                padding: 12px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #365899;
            }
        """)
        self.login_button.clicked.connect(self.login)
        layout.addWidget(self.login_button)

        # Sign Up Button
        self.signup_button = QPushButton("Sign Up")
        self.signup_button.setFont(QFont("Arial", 12))
        self.signup_button.setStyleSheet("""
            QPushButton {
                background-color: #36a420;
                color: white;
                padding: 12px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #65C3A1;
            }
        """)
        self.signup_button.clicked.connect(self.sign_up)
        layout.addWidget(self.signup_button)

        self.init_db()

    def init_db(self):
        """Initialize the SQLite3 database and create tables if they don't exist."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            year INTEGER
        )
        """)

        conn.commit()
        conn.close()

    def login(self):
        """Handle login logic."""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Username and password are required!")
            return

        # Close the login window and show the loading window
        self.close()
        self.loading_window = LoadingAnimation()
        self.loading_window.show()

        # Perform database query in the background
        QTimer.singleShot(2000, lambda: self.verify_credentials(username, password))

    def verify_credentials(self, username, password):
        """Verify user credentials."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user WHERE username = ? AND password = ?", (username, password))
        result = cursor.fetchone()
        conn.close()

        # Close the loading window
        self.loading_window.close()

        if result:
            self.open_main_app()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password!")
            self.show()  # Reopen the login window

    def open_main_app(self):
        """Open the main application window."""
        self.main_app = BookSearchApp()
        self.main_app.show()

    def sign_up(self):
        """Handle signup logic."""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Username and password are required!")
            return

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO user (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            QMessageBox.information(self, "Success", "Sign-up successful!")
            username = self.username_input.clear()
            password = self.password_input.clear()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "Username already exists!")
        finally:
            conn.close()

    def center_window(self):
        """Centers the window on the screen."""
        screen = QApplication.primaryScreen().geometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen.center())
        self.move(window_geometry.topLeft())


class LoadingAnimation(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)  # Frameless and floating
        self.setAttribute(Qt.WA_TranslucentBackground, True)  # Make the background transparent
        self.setFixedSize(200, 200)

        layout = QVBoxLayout()

        # QLabel for GIF
        gif_label = QLabel(self)
        gif_label.setAttribute(Qt.WA_TranslucentBackground, True)  # Transparent QLabel background
        layout.addWidget(gif_label)

        # Load and play GIF
        movie = QMovie("assets/loading.gif")  # Path to your GIF
        gif_label.setMovie(movie)
        movie.start()

        container = QWidget(self)
        container.setLayout(layout)
        container.setAttribute(Qt.WA_TranslucentBackground, True)  # Transparent container background
        self.setCentralWidget(container)


class FetchBooksThread(QThread):
    """Thread to fetch book data from Open Library API."""
    data_fetched = pyqtSignal(list, int)  # Signal includes books and total count

    def __init__(self, query, current_page=1, books_per_page=10):
        super().__init__()
        self.query = query
        self.current_page = current_page
        self.books_per_page = books_per_page

    def run(self):
        """Fetch data from Open Library API with optimized pagination."""
        try:
            # Use pagination parameters directly in the API query
            response = requests.get(
                f"https://openlibrary.org/search.json",
                params={
                    "q": self.query,
                    "page": self.current_page,
                    "limit": self.books_per_page,
                    "fields": "title,author_name,subject"
                },
                timeout=10  # Set a timeout to avoid long waits
            )

            if response.status_code == 200:
                data = response.json()
                books = data.get("docs", [])
                total_books = data.get("numFound", 0)

                # Process fetched data
                book_data = [
                    [
                        book.get("title", "Unknown Title"),
                        ", ".join(book.get("author_name", ["Unknown Author"])),
                        ", ".join(book.get("subject", ["Unknown Genre"])[:3])  # Limit genres to 3
                    ]
                    for book in books
                ]

                self.data_fetched.emit(book_data, total_books)
            else:
                # Emit empty data in case of a failed response
                self.data_fetched.emit([], 0)
        except Exception as e:
            print(f"Error fetching books: {e}")
            self.data_fetched.emit([], 0)



class BookSearchApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.auth_window = None
        self.setWindowTitle("Book Search App")
        self.setWindowFlags(Qt.FramelessWindowHint)  # Remove title bar
        self.showMaximized()

        self.init_ui()
        self.fetch_initial_books()

    def init_ui(self):
        """Initialize the main UI layout."""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Main layout
        self.layout = QVBoxLayout(self.central_widget)

        # Top bar with logo and burger menu
        self.top_bar = QHBoxLayout()

        # Burger menu
        self.burger_menu_button = QPushButton("☰")
        self.burger_menu_button.setFixedSize(70, 30)
        self.burger_menu_button.setFont(QFont("Arial", 14, QFont.Bold))
        self.burger_menu_button.clicked.connect(self.open_burger_menu)

        self.menu = QMenu()
        self.logout_action = QAction("Logout", self)
        self.menu.addAction(self.logout_action)


        # Connect the logout action's clicked signal to the open_auth method
        self.logout_action.triggered.connect(self.open_auth)
        self.burger_menu_button.setMenu(self.menu)

        # Logo placeholder
        self.logo_label = QLabel("LOGO")
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setStyleSheet("font-size: 20px; font-weight: bold;")

        self.top_bar.addWidget(self.burger_menu_button)
        self.top_bar.addStretch()
        self.top_bar.addWidget(self.logo_label)
        self.top_bar.addStretch()

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search for books...")
        self.search_bar.setStyleSheet("font-size: 30px; padding: 10px;")
        self.search_bar.returnPressed.connect(self.fetch_books)

        # Book table
        self.book_table = QTableWidget()
        self.book_table.setColumnCount(3)  # Number of columns
        self.book_table.setHorizontalHeaderLabels(["Title", "Author", "Genre"])
        self.book_table.setStyleSheet("font-size: 25px;")
        self.book_table.horizontalHeader().setStretchLastSection(False)

        # Balance column sizes
        header = self.book_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)  # Distribute space equally among columns

        # Remove grid lines and row numbers
        self.book_table.setShowGrid(False)  # Remove grid lines
        self.book_table.verticalHeader().setVisible(False)  # Hide row numbers

        self.book_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Disable editing

        # Loading spinner
        self.spinner = QLabel()
        self.movie = QMovie("assets/loading.gif")  # Add a spinner.gif file in your directory
        self.spinner.setMovie(self.movie)
        self.spinner.setAlignment(Qt.AlignCenter)

        # Stacked layout to switch between loading spinner and book table
        self.stacked_layout = QStackedLayout()
        self.stacked_layout.addWidget(self.book_table)
        self.stacked_layout.addWidget(self.spinner)

        # Pagination
        self.pagination_layout = QHBoxLayout()
        self.pagination_layout.addStretch()

        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.load_previous_page)
        self.pagination_layout.addWidget(self.prev_button)

        self.page_label = QLabel("Page 1")
        self.page_label.setAlignment(Qt.AlignCenter)
        self.pagination_layout.addWidget(self.page_label)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.load_next_page)
        self.pagination_layout.addWidget(self.next_button)

        self.pagination_layout.addStretch()

        # Add widgets to main layout
        self.layout.addLayout(self.top_bar)
        self.layout.addWidget(self.search_bar)
        self.layout.addLayout(self.stacked_layout)
        self.layout.addLayout(self.pagination_layout)

        # Pagination data
        self.current_page = 1
        self.total_pages = 1
        self.books_per_page = 10

    def load_previous_page(self):
        """Load the previous page of books."""
        if self.current_page > 1:
            self.current_page -= 1
            self.fetch_books()

    def load_next_page(self):
        """Load the next page of books."""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.fetch_books()

    def update_page_label(self):
        """Update the page label to reflect the current page."""
        self.page_label.setText(f"Page {self.current_page} of {self.total_pages}")

    def open_auth(self):
        # Create a QMessageBox instance
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setText("Are you sure you want to log out?")
        msg_box.setWindowTitle("Confirmation")

        # Add an OK button and no Cancel button (handled by the X button)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.button(QMessageBox.Ok).setText("OK")

        # Show the message box and capture the result
        result = msg_box.exec_()

        if result == QMessageBox.Ok:
            # Proceed with logout
            self.close()  # Close the current window
            self.auth_window = Auth()  # Create an instance of the Auth window
            self.auth_window.show()  # Show the Auth window
        else:
            # Cancel the logout action
            pass

    def fetch_initial_books(self):
        """Fetch a default set of books when the app starts."""
        self.switch_to_spinner()
        self.thread = FetchBooksThread("bestsellers", current_page=1, books_per_page=self.books_per_page)
        self.thread.data_fetched.connect(self.display_books)
        self.thread.start()

    def fetch_books(self):
        """Fetch books based on the search query and current page."""
        query = self.search_bar.text().strip()
        if not query:
            return

        self.switch_to_spinner()
        self.thread = FetchBooksThread(query, current_page=self.current_page, books_per_page=self.books_per_page)
        self.thread.data_fetched.connect(self.display_books)
        self.thread.start()

    def switch_to_spinner(self):
        """Switch to the loading spinner."""
        self.spinner.show()
        self.movie.start()
        self.stacked_layout.setCurrentWidget(self.spinner)

    def switch_to_book_list(self):
        """Switch to the book list."""
        self.movie.stop()
        self.spinner.hide()
        self.stacked_layout.setCurrentWidget(self.book_table)

    def display_books(self, books, total_books):
        """Display the fetched books in the table and update pagination."""
        self.book_table.setRowCount(0)
        if books:
            for row_idx, book in enumerate(books):
                self.book_table.insertRow(row_idx)
                for col_idx, data in enumerate(book):
                    self.book_table.setItem(row_idx, col_idx, QTableWidgetItem(data))
        else:
            self.book_table.setRowCount(1)
            self.book_table.setItem(0, 0, QTableWidgetItem("No results found."))

        # Update total pages and page label
        self.total_pages = (total_books + self.books_per_page - 1) // self.books_per_page
        self.update_page_label()
        self.switch_to_book_list()

    def open_burger_menu(self):
        """Show the burger menu."""
        self.menu.exec_(self.burger_menu_button.mapToGlobal(Qt.Point(0, 30)))


def main():
    app = QApplication(sys.argv)
    window = Auth()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
