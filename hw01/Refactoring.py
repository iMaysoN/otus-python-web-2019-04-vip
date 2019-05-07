import ast
import os
import collections

from nltk import pos_tag

DEEP_SIZE = 100


def flat(list_of_objects):
    """ [(1,2), (3,4)] -> [1, 2, 3, 4]"""
    return sum([list(item) for item in list_of_objects], [])


def is_verb(word_to_check):
    if not word_to_check:
        return False
    pos_info = pos_tag([word_to_check])[0]
    word_tag = pos_info[1]
    return word_tag == 'VB'


def get_trees_from_path(target_path, with_file_names=False, with_file_content=False):
    """Generate list of trees by path"""
    file_names = get_file_names_from_path(target_path, DEEP_SIZE)
    trees = []
    for file_name in file_names:
        tree = generate_tree_from_file_name(file_name, with_file_names, with_file_content)
        trees.append(tree)
    print('trees generated')
    return trees


def get_file_names_from_path(target_path, nesting_size: int):
    """Get all file names from path"""
    file_names = []
    for dir_name, dirs, files in os.walk(target_path):
        python_files = [file for file in files if file.endswith('.py')]
        for python_file in python_files[:nesting_size]:
            file_names.append(os.path.join(dir_name, python_file))
    print('total %s files' % len(file_names))
    return file_names


def generate_tree_from_file_name(file_name, with_file_names, with_file_content):
    """Create list of trees with additional info if needed"""
    with open(file_name, 'r', encoding='utf-8') as opened_file:
        file_content = opened_file.read()
        parsed_tree = parse_tree_or_none(file_content)

        if with_file_names:
            if with_file_content:
                tree = (file_name, file_content, parsed_tree)
            else:
                tree = (file_name, parsed_tree)
        else:
            tree = (parsed_tree)
    return tree


def parse_tree_or_none(file_content):
    """Try parse tree by file content or return None"""
    try:
        parsed_tree = ast.parse(file_content)
    except SyntaxError as e:
        print(e)
        parsed_tree = None
    return parsed_tree


def get_all_names(tree):
    """Filter and collect names"""
    return [node.id for node in ast.walk(tree) if isinstance(node, ast.Name)]


def get_verbs_from_function_name(function_name):
    """Filter and collect verbs"""
    return [word for word in function_name.split('_') if is_verb(word)]


def get_all_words_in_path(path):
    """Get all names and separate by names"""
    trees = [t for t in get_trees_from_path(path) if t]
    names = flat([get_all_names(t) for t in trees])
    function_names = [name for name in names if is_function_name(name)]
    return flat([split_snake_case_name_to_words(function_name) for function_name in function_names])


def is_function_name(name):
    """If name like __function__ - these aren't function you're looking for"""
    return not (name.startswith('__') and name.endswith('__'))


def split_snake_case_name_to_words(name):
    """['this', 'name'] -> this_name"""
    return [n for n in name.split('_') if n]


def get_top_verbs_in_path(path, top_size=10):
    trees = [t for t in get_trees_from_path(path) if t]
    lower_names = flat(
        [[node.name.lower() for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)] for tree in trees])
    function_names = [name for name in lower_names if is_function_name(name)]
    print('functions extracted')
    verbs = flat([get_verbs_from_function_name(function_name) for function_name in function_names])
    return collections.Counter(verbs).most_common(top_size)


def get_top_functions_names_in_path(path, top_size=10):
    t = get_trees_from_path(path)
    nms = [f for f in
           flat([[node.name.lower() for node in ast.walk(t) if isinstance(node, ast.FunctionDef)] for t in t]) if
           is_function_name(f)]
    return collections.Counter(nms).most_common(top_size)


TOP_SIZE = 200

if __name__ == '__main__':
    wds = []
    projects = [
        'django',
        'flask',
        'pyramid',
        'reddit',
        'requests',
        'sqlalchemy',
    ]
    for project in projects:
        path = os.path.join('.', project)
        wds += get_top_verbs_in_path(path)

    print('total %s words, %s unique' % (len(wds), len(set(wds))))
    for word, occurrence in collections.Counter(wds).most_common(TOP_SIZE):
        print(word, occurrence)
