import os
import glob


def get_input_file_paths(input_path, file_extensions=None, verbose=False):
    """
    Get path to all input files to traverse
    :param input_path: path to input .tex file or directory with .tex files
    :param file_extensions: input file extensions. If None,
        files of all extensions will be considered.
    :param verbose: flag. If True, print details
    :return: list of files to traverse
    """
    # input is a file
    if is_file(input_path):
        if has_matching_extension(input_path, file_extensions):
            input_file_paths = [input_path]
            if verbose:
                print("Input file is registered.", verbose)
            return input_file_paths
        else:
            raise Exception("Incorrect input: file extension should be in : " + str(file_extensions))

    # input is a directory
    if is_directory(input_path):
        input_file_paths = find_path_to_dir_files_recursively(input_path, file_extensions)
        if verbose:
            print("Input registered: input is a directory with", len(input_file_paths),
                  "files with", file_extensions, "extensions")
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

