def index_all(search_list, item):
    """Return a list of lists containing the indices of item in search_list.
    search_list can be a nested list, and the function will search all
    sublist. The returned list will have the same structure as search_list.
    """
    index_list = []
    for index, value in enumerate(search_list):
        if value == item:
            # if the item is found, add the index to the list
            index_list.append([index])
            # append a list containing the index, because we need to keep the
            # same structure as the search_list, and the index is the only
            # information we have at this point
            # append a list containing the index, because we need to keep the
            # same structure as the search_list, and the index is the only
            # information we have at this point. This is important if the item
            # is found in a nested list: we need to keep track of the index
            # of the item in the nested list, in addition to the index of the
            # nested list itself.
        elif isinstance(value, list):
            # isinstance is a built-in function that takes two arguments, and
            # returns True if the first argument is an instance of the second
            # argument, and False otherwise. In this case, we are using it to
            # check if value is a list. If it is, we call index_all on it, and
            # add the results to the list. If it is not, we do nothing.
            # if the value is a list, search it and add the results to the list
            for i in index_all(value, item):
                index_list.append([index] + i)
    return index_list


# commands used in solution video for reference
if __name__ == '__main__':
    example = [[[1, 2, 3], 2, [1, 3]], [1, 2, 3]]
    print(index_all(example, 2))  # [[0, 0, 1], [0, 1], [1, 1]]
    print(index_all(example, [1, 2, 3]))  # [[0, 0], [1]]
