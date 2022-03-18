import os
import sys
import argparse
import traceback
import glob
import re

# local imports
from Abbreviation import Abbreviation
from json_converters.abbreviations_to_json import abbreviations_to_json


def main():
    # import current directory and it's subdirectories into system path for the current console
    # this would allow to import project modules without adding the project to the PYTHONPATH
    this_dir = os.path.dirname(__file__)
    sys.path.append(this_dir)

    # general arguments
    parser = argparse.ArgumentParser(description='The script finds abbreviations in a .tex file '
                                                 'or a folder with .tex files. The found abbreviations '
                                                 'are saved in output JSON file.')

    parser.add_argument('-i', metavar='--input', type=str, action='store', required=True,
                        help='path to input file or input files directory')

    parser.add_argument('-o', metavar='--output', type=str, action='store', default="./abbr.json",
                        help='path to output JSON file with abbreviations')

    # general flags
    parser.add_argument('--verbose', help="print details", action="store_true", default=False)

    # parse arguments
    args = parser.parse_args()

    input_path = args.i
    output_path = args.o
    verbose = args.verbose

    try:
        input_file_paths = get_input_file_paths(input_path, verbose)
        abbreviations = find_abbreviations_in_files_list(input_file_paths, verbose)
        abbreviations_to_json(abbreviations, output_path)
        if verbose:
            print("Total abbreviations found: ", len(abbreviations))
            print("Short notices: ", [abbreviation.short for abbreviation in abbreviations])

    except Exception as e:
        print("Abbreviations search error: " + str(e))
        traceback.print_tb(e.__traceback__)


def get_input_file_paths(input_path, verbose=False):
    """
    Get path to all input files to traverse
    :param input_path: path to input .tex file or directory with .tex files
    :param verbose: flag. If True, print details
    :return: list of files to traverse
    """
    # input is a file
    if is_file(input_path):
        if has_matching_extension(input_path, ["tex"]):
            input_file_paths = [input_path]
            print_or_skip("Input registered: input is a tex file", verbose)
            return input_file_paths
        else:
            raise Exception("Incorrect input: latex (.tex) file was expected")

    # input is a directory
    if is_directory(input_path):
        input_file_paths = find_path_to_dir_files_recursively(input_path, ["tex"])
        print_or_skip("Input registered: input is a directory with " +
                      str(len(input_file_paths)) + " .tex files", verbose)
        return input_file_paths

    # input is not a file or directory
    raise Exception("Wrong input: existing file or files directory is expected.")


def is_directory(path):
    return os.path.isdir(path)


def is_file(path):
    return os.path.isfile(path)


def find_path_to_dir_files_recursively(input_dir, file_extensions=None):
    file_paths = []
    # add file paths without filtering
    if file_extensions is None:
        for f in glob.glob(str(os.path.join(input_dir, "**")), recursive=True):
            file_paths.append(f)

    # add file paths only after filtering
    else:
        for f in glob.glob(str(os.path.join(input_dir, "**")), recursive=True):
            if has_matching_extension(f, file_extensions):
                file_paths.append(f)
    return file_paths


def has_matching_extension(file_path, extensions):
    for extension in extensions:
        if file_path.endswith("." + extension):
            return True
    return False


def find_abbreviations_in_files_list(file_paths, verbose):
    """
    Visit a number of input files and try to find abbreviations there
    :param file_paths: list of paths to input files
    :param verbose: flag. If True, print details
    :return: abbreviations: list of  abbreviations found in the input files
    """
    abbreviations = []
    for path in file_paths:
        file_abbreviations = find_abbreviations_in_file(path, verbose)
        for abbreviation in file_abbreviations:
            if abbreviation not in abbreviations:
                abbreviations.append(abbreviation)
    return abbreviations


def find_abbreviations_in_file(file_path, verbose):
    """
    Visit an input file and try to find abbreviations there
    :param file_path: path to input file
    :param verbose: flag. If True, print details
    :return: abbreviations: list of  abbreviations found in the input file
    """
    if verbose:
        print("Opening", file_path)
    abbreviations = []
    lines_with_two_round_brackets = get_lines_with_two_brackets(file_path)
    lines_with_two_round_brackets_ids = [key for key in lines_with_two_round_brackets.keys()]
    # print("  - lines with two brackets:", lines_with_two_round_brackets_ids)
    for line_id in lines_with_two_round_brackets_ids:
        line_abbreviations = try_find_abbreviations_in_line(lines_with_two_round_brackets[line_id])
        for line_abbreviation in line_abbreviations:
            line_abbreviation.file = file_path
            line_abbreviation.line = line_id
            if line_abbreviation not in abbreviations:
                abbreviations.append(line_abbreviation)
    if verbose:
        if len(abbreviations) > 0:
            print("   abbreviations found:", [str(abbreviation) for abbreviation in abbreviations])
    return abbreviations


def get_lines_with_two_brackets(file_path):
    """
    Get text lines that have both round brackets: '(' and ')'
    :param file_path: path to the text file
    :return: lines that have at least one bracket
            dictionary with key = line_id, value = line
    """
    lines_with_brackets = {}

    with open(file_path) as fp:
        line = fp.readline()
        line_id = 1
        while line:
            line = fp.readline()
            line_id += 1
            if has_two_round_brackets(line):
                lines_with_brackets[line_id] = line
    return lines_with_brackets


def try_find_abbreviations_in_line(line):
    """
    Try to find abbreviations in a line
    :param line: line of a text
    :return: list of abbreviations found in the text line
    """
    abbreviations = []
    substrings_in_round_brackets = find_substrings_in_round_brackets(line)
    for substring in substrings_in_round_brackets:
        if is_abbreviation(substring):
            abbreviation = Abbreviation(substring)
            abbreviations.append(abbreviation) # substring
    return abbreviations


def is_abbreviation(substrings_in_round_brackets):
    """
    Try to determine if a substring, enclosed in round brackets is
    an abbreviation
    :param substrings_in_round_brackets: substring, enclosed in round brackets
    :return: True, if a substring, enclosed in round brackets is
        an abbreviation, and False otherwise
    """
    # abbreviations do not start with i.e.,
    if substrings_in_round_brackets.strip().startswith("i.e."):
        return False

    # abbreviations do not start with e.g.,
    if substrings_in_round_brackets.strip().startswith("e.g."):
        return False

    # abbreviation has at least two capital letters
    if count_capital_letters(substrings_in_round_brackets) < 2:
        return False

    # in all other cases, we assume that the input substring,
    # enclosed in round brackets is an abbreviation
    return True


def count_capital_letters(string):
    """
    Count number of capital letters in a string
    :param string: string
    :return: number of capital letters in a string
    """
    capital_letters_num = sum(map(str.isupper, string))
    return capital_letters_num


def find_substrings_in_round_brackets(line):
    """
    Find all substrings enclosed in round brackets '()' that are in a line
    :param line: text line
    :return: all substrings enclosed in round brackets '()' that are in a line
    """
    matches = re.findall(r"\(([A-Za-z0-9_]+)\)", line)
    return matches


def get_lines_with_brackets(file_path):
    """
    Get text lines that have at least one round racket: '(' or ')'
    :param file_path: path to the text file
    :return: lines that have at least one bracket:
        dictionary with key = line_id, value = line
    """
    lines_with_brackets = {}

    with open(file_path) as fp:
        line = fp.readline()
        line_id = 1
        while line:
            line = fp.readline()
            line_id += 1
            if has_opening_bracket(line) or has_closing_bracket(line):
                lines_with_brackets[line_id] = line

    return lines_with_brackets


def has_two_round_brackets(line):
    """
    Check if a line of text has two round brackets.
    If yes, the line might contain an abbreviation
    :param line: Line of text
    :return: true, if a line of text has two brackets:
        an opening one, i.e., '(' and a closing one, i.e., ')'.
    """
    if has_opening_bracket(line):
        if has_closing_bracket(line):
            return True
    return False


def has_opening_bracket(line):
    """
    Check if a line of text has an opening bracket, i.e., '('
    If yes, the line might contain an abbreviation
    :param line: Line of text
    :return: true, if a line of text has an opening bracket, i.e., '('
    """
    return "(" in line


def has_closing_bracket(line):
    """
    Check if a line of text has an closing bracket, i.e., ')'
    If yes, the line might contain an abbreviation
    :param line: Line of text
    :return: true, if a line of text has a closing bracket, i.e., ')'
    """
    return ")" in line


def print_or_skip(message, verbose):
    if verbose:
        print(message)


if __name__ == "__main__":
    main()