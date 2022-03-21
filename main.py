import os
import sys
import argparse
import traceback
import re
import copy

# local imports
from Abbreviation import Abbreviation
from json_converters.abbreviations_to_json import abbreviations_to_json
from input_file_worker import get_input_file_paths


def main():
    # import current directory and it's subdirectories into system path for the current console
    # this would allow importing project modules without adding the project to the PYTHONPATH
    this_dir = os.path.dirname(__file__)
    sys.path.append(this_dir)

    # general arguments
    parser = argparse.ArgumentParser(description='The script finds abbreviations in a .tex file '
                                                 'or a folder with .tex files. The found abbreviations '
                                                 'are saved in output JSON file.')

    parser.add_argument('-i', metavar='--input', type=str, action='store', required=True,
                        help='path to input file or input files directory')

    parser.add_argument('-o', metavar='--output', type=str, action='store', default="./output/abbr.json",
                        help='path to output JSON file with abbreviations')

    parser.add_argument('-e', metavar='--extension', type=str, action='store', default='tex',
                        help='file extension. Only files of this extension will be searched')

    # general flags
    parser.add_argument('--verbose', help="print details", action="store_true", default=False)

    # parse arguments
    args = parser.parse_args()

    input_path = args.i
    output_path = args.o
    extension = args.e
    verbose = args.verbose

    try:
        input_file_paths = get_input_file_paths(input_path, [extension], verbose)
        abbreviations = find_abbreviations_in_files_list(input_file_paths, verbose)
        abbreviations_to_json(abbreviations, output_path)
        if verbose:
            print("Total abbreviations found: ", len(abbreviations))
            print("Short notices: ", [abbreviation.short for abbreviation in abbreviations])

    except Exception as e:
        print("Abbreviations search error: " + str(e))
        traceback.print_tb(e.__traceback__)


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
    file_as_lines = get_file_as_lines(file_path)
    line_id = 0
    for line in file_as_lines:
        if has_two_round_brackets(line):
            prev_line = file_as_lines[line_id-1] if line_id > 0 else ""
            line_abbreviations = try_find_abbreviations_in_line(line, prev_line)
            for line_abbreviation in line_abbreviations:
                line_abbreviation.file = file_path
                line_abbreviation.line = line_id
                if line_abbreviation not in abbreviations:
                    abbreviations.append(line_abbreviation)
        line_id += 1
    if verbose:
        if len(abbreviations) > 0:
            print("   abbreviations found:", [str(abbreviation) for abbreviation in abbreviations])
    return abbreviations


def get_file_as_lines(file_path):
    """
    Get file represented as an array of lines
    :param file_path: path to file
    :return: file represented as an array of lines
    """
    lines = []

    with open(file_path) as fp:
        line = fp.readline()
        lines.append(line)
        while line:
            line = fp.readline()
            lines.append(line)
    return lines


def try_find_abbreviations_in_line(line, prev_line):
    """
    Try to find abbreviations in a line
    :param line: line of text that may contain abbreviations
    :param prev_line: line, previous to current line (if available)
    :return: list of abbreviations found in the text line
    """
    abbreviations = []
    substrings_in_round_brackets = find_substrings_in_round_brackets(line)
    for substring in substrings_in_round_brackets:
        if is_abbreviation(substring):
            abbreviation = Abbreviation(substring)
            long_notice = find_long_notice(line, prev_line, substring)
            if long_notice is not None:
                abbreviation.long = long_notice
            abbreviations.append(abbreviation) # substring
    return abbreviations


def find_long_notice(line: str, prev_line: str, short_notice: str):
    """
    Find long notice for the abbreviation
    :param line: text line with abbreviation
    :param prev_line: line, previous to the text line with abbreviation (if available)
    :param short_notice: short notice of abbreviation, e.g., BBC
    :return: long notice of abbreviation, e.g., British Broadcasting Corporation
    """
    # find position of short notice in the line
    short_notice_pos = line.find(short_notice)

    short_notice_letters = [char for char in short_notice]
    # small "s" in the end of abbreviation stands for multiple objects
    if short_notice_letters[-1] == "s":
        short_notice_letters.pop(-1)

    print("short notice letters: ", short_notice_letters)

    # the long notice should be located before the abbreviation
    substring_to_search = line[:short_notice_pos]
    # also, sometimes (part of) the long notice can be located in the previous line
    substring_to_search = prev_line + substring_to_search

    print("substring_to_search", substring_to_search)
    long_notice = search_substring_for_long_notice(substring_to_search, short_notice_letters)

    return long_notice


def search_substring_for_long_notice(substring: str, short_notice_letters: []):
    """"
    Search substring of text for long notice of abbreviation, e.g., British Broadcasting Corporation
    :param substring: substring to search
    :param short_notice_letters: short notice of abbreviation, e.g., BBC, represented as an array of letters
    :return: long notice of abbreviation (e.g., British Broadcasting Corporation) if one is found
        and None otherwise
    """

    # we search string word-by word
    string_as_words = substring.split(" ")

    # we start search from the last letter/word
    # thus, we traverse the short-notice letters
    # and obtain respective long-notice words in reverse order
    long_notice_words_reverse = []

    # current letter position (last letter in the short notice)
    letter_id = len(short_notice_letters) - 1

    # current word position (last word in the substring)
    word_id = len(string_as_words) - 1

    # the search stops when:
    # 1) all letters were traversed OR
    # 2) all substring was traversed OR
    # 3) the long notice cannot be found in the substring
    long_notice_is_in_substring = True
    while letter_id >= 0 and word_id >= 0 and long_notice_is_in_substring:
        cur_letter = short_notice_letters[letter_id]
        cur_word = string_as_words[word_id]

        # skip "words" that are punctuation
        while cur_word in ["(", ")", ".", ",", ";"] and word_id > 0:
            word_id -= 1
            cur_word = string_as_words[word_id]

        # print("CUR LETTER: ", short_notice_letters[letter_id], "CUR WORD: ", string_as_words[word_id])
        # check if this still looks like the long notice
        if not cur_word.startswith(cur_letter) and not cur_word.startswith(cur_letter.lower()):
            long_notice_is_in_substring = False

        # if hyphen is present in the word, the word
        # corresponds to several letters in the abbreviation
        if "-" in cur_word:
            cur_word_parts = cur_word.split("-")
            sub_words_cnt = len(cur_word_parts)
            long_notice_words_reverse.append(cur_word)
            word_id -= sub_words_cnt
            letter_id -= sub_words_cnt
        # otherwise, the word corresponds to only
        # one letter in the abbreviation
        else:
            long_notice_words_reverse.append(cur_word)
            word_id -= 1
            letter_id -= 1

    if not long_notice_is_in_substring:
        return None

    long_notice = form_long_notice_from_reversed_words_list(long_notice_words_reverse)
    return long_notice


def form_long_notice_from_reversed_words_list(long_notice_words_reverse):
    # print("long_notice_words_reverse", long_notice_words_reverse)
    long_notice = ""
    long_notice_words_reverse.reverse()
    for word in long_notice_words_reverse:
        long_notice += word + " "
    long_notice.strip()
    return long_notice


# OLD
"""
def search_substring_for_long_notice(substring: str, short_notice_letters: []):

    Search substring of text for long notice of abbreviation, e.g., British Broadcasting Corporation
    :param substring: substring to search
    :param short_notice_letters: short notice of abbreviation, e.g., BBC, represented as an array of letters
    :return: long notice of abbreviation (e.g., British Broadcasting Corporation) if one is found
        and None otherwise

    # we start search from the last letter/word
    short_notice_letters_reversed = copy.deepcopy(short_notice_letters)
    short_notice_letters_reversed.reverse()

    long_notice_words_reverse = []
    # search positions in substring
    start_pos = 0
    end_pos = len(substring) - 1

    for letter in short_notice_letters_reversed:
        word, word_pos_in_string = find_word_and_its_pos_in_string(substring, letter, start_pos, end_pos)
        # if at least one word was not found, we consider the long notice not found
        if word is None:
            return None

        long_notice_words_reverse.append(word)
        end_pos = word_pos_in_string

    long_notice = ""
    long_notice_words_reverse.reverse()
    for word in long_notice_words_reverse:
        long_notice += word + " "
    long_notice.strip()

    return long_notice
 """


def find_word_and_its_pos_in_string(string, first_letter, start_pos, end_pos):
    string_as_words = string.split(" ")
    word_id = len(string_as_words) - 1

    word_pos_in_str = end_pos
    while word_id > 0:
        cur_word = string_as_words[word_id]
        word_pos_in_str -= len(cur_word)
        if cur_word.startswith(first_letter) or cur_word.startswith(first_letter.lower()):
            return cur_word, word_pos_in_str
        word_id -= 1

    return None, -1


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


if __name__ == "__main__":
    main()