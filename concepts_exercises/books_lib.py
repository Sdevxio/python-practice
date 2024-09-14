from typing import List


class Book:
    def __init__(self, title, author, isbn):
        self._title = title
        self._author = author
        self._isbn = isbn

    def __str__(self):
        return f"{self._title} by {self._author} (ISBN: {self._isbn})"

    @property
    def isbn(self):
        return self._isbn


class Library:
    def __init__(self):
        self._books = []

    def init(self):
        self._books: List[Book] = []

    def add_book(self, book):
        self._books.append(book)
        print(f"Added: {book}")

    def remove_book(self, isbn):
        for book in self._books:
            if book.isbn == isbn:
                self._books.remove(book)
                print(f"Removed: {book}")
                return
        print(f"Book with ISBN {isbn} not found.")

    def display_books(self):
        if not self._books:
            print("The library is empty.")
        else:
            print("Library books:")
            for book in self._books:
                print(book)

    def __str__(self):
        return f"Library with {len(self._books)} books"


if __name__ == '__main__':
    library = Library()
    book1 = Book("Python Crash Course", "Eric Matthes", "1593279280")
    book2 = Book("Clean Code", "Robert C. Martin", "0132350882")
    library.add_book(book1)
    library.add_book(book2)
    print(library)
    library.display_books()
    library.remove_book("1593279280")
    library.display_books()
