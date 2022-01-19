# This code as to be ran in a Maya able to use 'dwpicker' package.
import os
from dwpicker.ingest import animschool


SOURCE_DIRECTORY = "" # Replace those variables before conversion
DESTINATION_DIRECTORY = ""

for f in os.listdir(SOURCE_DIRECTORY):
    if not f.lower().endswith(".pkr"):
        continue
    filepath = os.path.join(SOURCE_DIRECTORY, f)
    animschool.convert(filepath, DESTINATION_DIRECTORY)