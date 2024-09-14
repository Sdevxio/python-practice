class Book:
    def __init__(self, title, author, isbn):
        self._title = title
        self._author = author
        self._isbn = isbn
        self._is_borrowed = False

    def get_title(self):
        return self._title

    def get_author(self):
        return self._author

    def get_isbn(self):
        return self._isbn

    def is_borrowed(self):
        return self._is_borrowed

    def set_borrowed(self, status):
        self._is_borrowed = status


class Member:
    def __init__(self, name, member_id):
        self._name = name
        self._member_id = member_id
        self._borrowed_books = []

    def get_name(self):
        return self._name

    def get_member_id(self):
        return self._member_id

    def borrow_book(self, book):
        self._borrowed_books.append(book)

    def member_return_book(self, book):
        self._borrowed_books.remove(book)

    def get_borrowed_books(self):
        return self._borrowed_books


class Library:
    def __init__(self):
        self._books = []
        self._members = []

    def add_book(self, book):
        self._books.append(book)

    def add_member(self, member_name):
        self._members.append(member_name)

    def borrow_book(self, member_name, book_title):
        for book in self._books:
            if book.get_title() == book_title and not book.is_borrowed():
                book.set_borrowed(True)
                member_name.borrow_book(book)
                return True
        return False

    def return_book(self, member_name, book_title):
        for book in member_name.get_borrowed_books():
            if book.get_title() == book_title:
                book.set_borrowed(False)
                member_name.member_return_book(book)
                return True
        return False

    def display_books(self):
        for book in self._books:
            print(f"{book.get_title()} by {book.get_author()} (ISBN: {book.get_isbn()})")

    def display_members(self):
        for member in self._members:
            print(f"{member.get_name()} (ID: {member.get_member_id()})")

    @property
    def members(self):
        return self._members


# Example usage
library = Library()

# Adding books
library.add_book(Book("The Great Gatsby", "F. Scott Fitzgerald", "9780743273565"))
library.add_book(Book("To Kill a Mockingbird", "Harper Lee", "9780446310789"))

# Adding members
library.add_member(Member("John Doe", "M001"))
library.add_member(Member("Jane Smith", "M002"))

# Displaying books and members
print("Books in the library:")
library.display_books()
print("\nLibrary members:")
library.display_members()

# Borrowing and returning books
member = library.members[0]
library.borrow_book(member, "The Great Gatsby")
print(f"\n{member.get_name()} borrowed The Great Gatsby")
library.return_book(member, "The Great Gatsby")
print(f"{member.get_name()} returned The Great Gatsby")
