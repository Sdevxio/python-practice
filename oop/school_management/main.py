from oop.school_management.school import School

if __name__ == '__main__':
    school = School()
    print(school.add_student("Paul", 15, 10))
    print(school.add_student("Alice", 20, 11))
    print(school.add_student("Alice", 20, 11))
    print(school.add_student("Ben", 21, 12))
    print(school.add_teacher("Mr. Josh", 35, "Math"))
    print(school.add_teacher("Ms. Liza", 50, "Science"))
    print(school.add_teacher("Ms. Diana", 36, "History"))

    print("\nListing people by name:")
    print(school.find_by_name("Ms. Diana").introduce())
    print(school.find_by_name("Ms. Liza"))
    print(school.find_by_name("Cara"))
    print("\nListing all people:")
    for school in school.list_all_people():
        print(school)
