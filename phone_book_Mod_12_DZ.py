from collections import UserDict
import datetime
import re
import pickle
import os

class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name] = record

    def iterator(self, count: int):
        for key, value in self:
            i = 1
            temp_dict = {}
            while i <= count:
                temp_dict[key] = value
                i += 1
            yield temp_dict

    def __iter__(self):
        for key, value in self.data.items():
            yield key, value

    def get_key_by_name(self, name):
        for key, value in self.data.items():
            if key.value == name:
                return key

class Field:
    def __init__(self, value=None):
        self._value = None
        self.value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value


class Birthday(Field):
    def days_to_birthday(self):
        birthday = self._value
        today = datetime.date.today()
        next_birthday = datetime.date(year=today.year, month=birthday.month, day=birthday.day)
        if next_birthday < today:
            next_birthday = datetime.date(year=today.year + 1, month=birthday.month, day=birthday.day)

        delta = next_birthday - today

        if delta.days == 0:
            return "Today birthday"
        else:
            return f"{delta.days} days to next birthday"

    @Field.value.setter
    def value(self, value):
        try:
            self._value = datetime.datetime.strptime(value, '%d-%m-%Y')
            # super(Birthday, self.__class__).value.fset(self, datetime.datetime.strptime(value, '%d-%m-%Y'))
        except ValueError:
            print("Incorrect data format, should be DD-MM-YYYY")


class Name(Field):
    pass


class PhoneFormatError(Exception):
    pass


class Phone(Field):

    def __init__(self, value):
        self.value = Phone.check_phone(value)

    @classmethod
    def check_phone(cls, value):
        regex = r"\([0-9]{3}\)[0-9]{3}-[0-9]{2}-[0-9]{2}"
        if len(re.findall(regex, value)) == 0:
            raise PhoneFormatError
        return value

    @Field.value.setter
    def value(self, value):
        self._value = Phone.check_phone(value)
        # super(Phone, self.__class__).value.fset(self, Phone.check_phone(value))


class Record:

    def __init__(self, name, phone=None, birthday=None):
        self.name = Name(name)
        self.birthday = None
        # self.birthday = Birthday()
        # if phone:
        #     self.phones = [Phone(phone)]
        # else:
        #     self.phones = []
        phones = []
        if phone:
            self.add_phone(phone)
        if birthday:
            self.birthday.value = birthday

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def delete_phone(self, phone):
        for elem in self.phones:
            if elem.value == phone:
                self.phones.remove(elem)

    def delete_phone_index(self, index):
        self.phones.pop(index)

    def edit_phone(self, old_phone, new_phone):
        for elem in self.phones:
            if elem.value == old_phone:
                elem.value = new_phone

if os.path.isfile('dump.pickle'):
    with open('dump.pickle', 'rb') as file:
        address_book = pickle.load(file)
else:
    address_book = AddressBook()


def error_handler(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return 'This contact doesnt exist, please try again.'
        except ValueError as exception:
            return exception.args[0]
        except IndexError:
            return 'This contact cannot be added, it exists already'
        except TypeError:
            return 'Unknown command or parametrs, please try again.'
        except PhoneFormatError:
            print("Incorrect phone format, (NNN)NNN-NN-NN")
    return inner

@error_handler
def add(*args):
    command_list = args[0]
    if len(command_list) < 2:
        print("Give me name and phone please")
        return
    contact_name = command_list[0]
    contact_phone = command_list[1]
    contact_birthday = None
    if len(command_list) > 2:
        contact_birthday = command_list[2]
    if contact_name not in address_book:
        new_record = Record(contact_name, contact_phone, contact_birthday)
        address_book.add_record(new_record)
    else:
        address_book[contact_name].add_phone(contact_phone)


@error_handler
def change_phone(*args):
    command_list = args[0]
    if len(command_list) != 3:
        print("Give me name, old and new phone please")
        return

    contact_name, contact_old_phone, contact_new_phone, *_ = command_list
    address_book[address_book.get_key_by_name(contact_name)].edit_phone(contact_old_phone, contact_new_phone)
    # if not len(command_list) == 3:
    #     print("Give me name, old and new phone please")
    #     return
    # # name, old_phone, new_phone, *_ = command_list
    # contact_name = command_list[0]
    # contact_old_phone = command_list[1]
    # contact_new_phone = command_list[2]
    # address_book[contact_name].edit_phone(contact_old_phone, contact_new_phone)

@error_handler
def delete_phone(*args):
    command_list = args[0]
    if len(command_list) != 2:
        print("Give me name and phone please")
        return
    contact_name, contact_phone, *_ = command_list
    address_book[address_book.get_key_by_name(contact_name)].delete_phone(contact_phone)
    # contact_name = command_list[0]
    # contact_phone = command_list[1]
    # address_book[contact_name].delete_phone(contact_phone)


@error_handler
def show():
    for elem in address_book.iterator(10):
        for key, data in elem.items():
            print(f"""Name: {key.value} {f" - Birthday: {data.birthday.value.strftime('%d-%m-%Y')} ({data.birthday.days_to_birthday()})" if data.birthday.value else ''}\nPhone: {', '.join(phone.value for phone in data.phones)}""")

@error_handler
def phone(*args):
    command_list = args[0]
    if len(command_list) != 1:
        print("Enter user name")
        return

    contact_name = args[0][0]
    print(address_book[contact_name])

@error_handler
def search(*args):
    command_list = args[0]
    if not command_list:
        print("Give me text for search")
        return

    search_text = command_list[0]

    for elem in address_book:
        data = elem[1]
        show_this_elem = data.name.value.lower().find(search_text) >= 0
        for phone in data.phones:
            if ''.join(filter(str.isdigit, phone.value)).find(search_text) >= 0:
                show_this_elem = True

        if show_this_elem:
            print(f"""Name: {data.name.value} {f" - Birthday: {data.birthday.value.strftime('%d-%m-%Y')} ({data.birthday.days_to_birthday()})" if data.birthday.value else ''}\nPhone: {', '.join(phone.value for phone in data.phones)}""")

def stop():
    with open('dump.pickle', 'wb') as file:
        pickle.dump(address_book, file)
    print("Good bye!")
    quit()


def hello(_):
    return "How can I help you?"

def exit(_):
    return "Good bye!"

@error_handler
def get_handler(command_list):
    return read_command_list(command_list)


def read_command_list(command_list: list):
    command = HANDLERS[command_list.pop(0).lower()]
    command = read_command_list(command_list) if command == read_command_list else command
    return command

HANDLERS = {
    "hello": hello,
    "good_bye": exit,
    "close": exit,
    "exit": exit,
    "add": add,
    "change": change_phone,
    "show_all": show,
    "show": read_command_list,
    "phone": phone,
    "delete": delete_phone,
    "search": search
}

def parser_input(user_input):
    cmd, *args = user_input.split()
    try:
        handler = HANDLERS[cmd.lower()]
    except KeyError:
        if args:
            cmd = f"{cmd} {args[0]}"
            args = args[1:]
        handler = HANDLERS[cmd.lower(), "Unknown command"]
    return handler, args

def main():
    while True:
        user_input = input(">>>")
        handler, *args = parser_input(user_input)
        result = handler(*args)
        if not result:
            print("Good bye!")
            break
        print(result)


if __name__ == "__main__":
    main()