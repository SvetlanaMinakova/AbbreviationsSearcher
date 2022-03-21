class Abbreviation:
    """
    An Abbreviation found in your text files
    Attributes:
        short: short notice (e.g., BBC)
        long: long notice (e.g., British Broadcasting Corporation)
        file: file where abbreviation was first defined
        line: line in the file where abbreviation was first defined
    """
    def __init__(self, short, long=None, file=None, line=None):
        self.short = short
        self.long = long
        self.line = line
        self.file = file

    def __eq__(self, other):
        return self.short == other.short

    def __str__(self):
        return "{" + self.short + "}"


def find_abbreviation_by_short_notice(short_notice, abbreviations):
    for abbreviation in abbreviations:
        if abbreviation.short == short_notice:
            return abbreviation
    return None

