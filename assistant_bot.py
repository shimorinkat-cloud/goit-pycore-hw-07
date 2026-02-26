from collections import UserDict
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import re


def input_error(func):
    """
    Decorator for handling user input errors.
    Catches common exceptions and returns user-friendly messages.
    """
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e)
        except KeyError:
            return "Contact not found."
        except IndexError:
            return "Enter required arguments."
    return inner


class Field:
    """
    Base class for all contact fields.
    """

    def __init__(self, value: str) -> None:
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class Name(Field):
    """Represents contact name."""
    pass


class Phone(Field):
    """
    Represents phone number.
    Must contain exactly 10 digits.
    """

    def __init__(self, value: str) -> None:
        if not re.fullmatch(r"\d{10}", value):
            raise ValueError("Phone number must contain exactly 10 digits.")
        super().__init__(value)


class Birthday(Field):
    """
    Represents birthday field.
    Date format: DD.MM.YYYY
    """

    def __init__(self, value: str) -> None:
        try:
            parsed_date = datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(parsed_date)


class Record:
    """
    Stores contact information:
    - Name
    - List of phones
    - Optional birthday
    """

    def __init__(self, name: str) -> None:
        self.name: Name = Name(name)
        self.phones: List[Phone] = []
        self.birthday: Optional[Birthday] = None

    def add_phone(self, phone: str) -> None:
        """Adds phone number to contact."""
        self.phones.append(Phone(phone))

    def change_phone(self, old_phone: str, new_phone: str) -> None:
        """Changes existing phone number."""
        for phone in self.phones:
            if phone.value == old_phone:
                self.phones.remove(phone)
                self.phones.append(Phone(new_phone))
                return
        raise ValueError("Old phone number not found.")

    def find_phone(self, phone: str) -> Optional[Phone]:
        """Finds phone number in contact."""
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def add_birthday(self, birthday: str) -> None:
        """Adds birthday to contact."""
        self.birthday = Birthday(birthday)

    def __str__(self) -> str:
        phones = "; ".join(phone.value for phone in self.phones)
        birthday = (
            self.birthday.value.strftime("%d.%m.%Y")
            if self.birthday
            else "Not set"
        )
        return f"Contact name: {self.name.value}, phones: {phones}, birthday: {birthday}"


class AddressBook(UserDict):
    """
    Stores and manages all contact records.
    """

    def add_record(self, record: Record) -> None:
        """Adds new contact record."""
        self.data[record.name.value] = record

    def find(self, name: str) -> Optional[Record]:
        """Finds record by name."""
        return self.data.get(name)

    def get_upcoming_birthdays(self) -> List[Dict[str, str]]:
        """
        Returns list of contacts who have birthdays
        within next 7 days.
        Weekend birthdays move to Monday.
        """
        today = datetime.today().date()
        upcoming_birthdays: List[Dict[str, str]] = []

        for record in self.data.values():
            if record.birthday:
                birthday = record.birthday.value.date()
                birthday_this_year = birthday.replace(year=today.year)

                if birthday_this_year < today:
                    birthday_this_year = birthday_this_year.replace(year=today.year + 1)

                delta_days = (birthday_this_year - today).days

                if 0 <= delta_days <= 7:
                    congratulation_date = birthday_this_year

                    if congratulation_date.weekday() >= 5:
                        congratulation_date += timedelta(days=7 - congratulation_date.weekday())

                    upcoming_birthdays.append({
                        "name": record.name.value,
                        "congratulation_date": congratulation_date.strftime("%d.%m.%Y")
                    })

        return upcoming_birthdays


def parse_input(user_input: str) -> tuple[str, List[str]]:
    """Parses user command and arguments."""
    cmd, *args = user_input.split()
    return cmd.lower(), args


@input_error
def add_contact(args: List[str], book: AddressBook) -> str:
    name, phone = args
    record = book.find(name)

    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    else:
        message = "Contact updated."

    record.add_phone(phone)
    return message


@input_error
def change_contact(args: List[str], book: AddressBook) -> str:
    name, old_phone, new_phone = args
    record = book.find(name)
    if record is None:
        raise KeyError
    record.change_phone(old_phone, new_phone)
    return "Phone updated."


@input_error
def show_phone(args: List[str], book: AddressBook) -> str:
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError
    return "; ".join(phone.value for phone in record.phones)


@input_error
def show_all(book: AddressBook) -> str:
    if not book.data:
        return "Address book is empty."
    return "\n".join(str(record) for record in book.data.values())


@input_error
def add_birthday(args: List[str], book: AddressBook) -> str:
    name, birthday = args
    record = book.find(name)
    if record is None:
        raise KeyError
    record.add_birthday(birthday)
    return "Birthday added."


@input_error
def show_birthday(args: List[str], book: AddressBook) -> str:
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError
    if record.birthday is None:
        return "Birthday not set."
    return record.birthday.value.strftime("%d.%m.%Y")


@input_error
def birthdays(book: AddressBook) -> str:
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No upcoming birthdays."
    return "\n".join(
        f"{item['name']} — {item['congratulation_date']}"
        for item in upcoming
    )


def main() -> None:
    """
    Entry point of assistant bot.
    """
    book = AddressBook()
    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(book))

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()