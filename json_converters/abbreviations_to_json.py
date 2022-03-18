import json
import os
import Abbreviation


def abbreviations_to_json(abbreviations: [Abbreviation], filepath: str):
    """
    Convert a target edge platform (architecture) into a JSON File
    :param abbreviations: list of abbreviations
    :param filepath: path to target .json file
    """
    json_abbreviations = []
    for abbreviation in abbreviations:
        abbreviation_as_dict = {"short": abbreviation.short}
        if abbreviation.long is not None:
            abbreviation_as_dict["long"] = abbreviation.long
        if abbreviation.file is not None:
            abbreviation_as_dict["file"] = abbreviation.file
        if abbreviation.line is not None:
            abbreviation_as_dict["line"] = abbreviation.line
        json_abbreviations.append(abbreviation_as_dict)

    abbreviations_as_dict = {"abbreviations": json_abbreviations}
    save_as_json(filepath, abbreviations_as_dict)


def save_as_json(abs_path, data_json, pretty_printing=True):
    """
    Write json file
    :param abs_path: abs path to .json file
    :param pretty_printing: make .json printing pretty
    :param data_json json string to be written into the file
    """
    # create parent directory for file, if it doesn't exist
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    with open(abs_path, 'w') as f:
        if pretty_printing:
            json.dump(data_json, f, indent=4)
        else:
            json.dump(data_json, f)

