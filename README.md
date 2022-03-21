### Script searches for abbreviations in a .tex file or a folder with .tex files

I am to lazy to search for abbreviations in my thesis by hand... So I do it using a script. Please, note, the script is not perfect. It merely helps with identifying abbreviations in your (.tex) files.

#### Example use
$ python main.py -i ./input_examples/ --verbose

**Expected output**
Opening ./input_examples/Introduction.tex
  - abbreviations found ( 7 ): ['{CNNs}', '{MPSoCs}', '{CPUs}', '{FPGAs}', '{DL}', '{SDF}', '{CSDF}']
Abbreviations saved in ./output/abbr.json

#### Example input
see ./input_examples/Introduction.tex

#### Example output
see ./output_examples/abbr.json