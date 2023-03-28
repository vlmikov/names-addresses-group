## GroupPeople VARIANT 1
GroupPeople is a Python class that processes a CSV file containing names addresses and retrieves their corresponding latitude and longitude 
coordinates from the Geoapify API based on their text information, compare the coordinates and get all names with same address.
The output is a CSV file that contains names. Each line is a commaseparated list of names of the people living at the same address. The
names in a line is sorted alphabetically. The lines of the file is
also sorted alphabetically.

This repository contains:
README.md

main.py            => The main.py file contains GroupPeople class and input logic in order to make the interaction with this script esier for users

constants.py       => This file contains Geoapify API key, and expected csv header

requirenments.txt  => All required dependencies

### Installation
To use this Python script, you must first clone or download the repository and install the required dependencies,
which can be found in the requirements.txt file. You can install them using pip:

1. Create script directory
```
mkdir group_people_script
cd group_people_script
```
2. Create virtual environment and activate it

```
# For macOS
python3 -m venv env
source env/bin/activate
```
3. Clone or download the repository

```
git clone https://github.com/vlmikov/names-addresses-group.git
```
4. Install requirenments.txt
```
pip3 install -r requirements.txt
```
5. Run the script
```
python3 main.py
```
You will also need to sign up for a free Geoapify API key https://www.geoapify.com/ or use my personal API key (provided by email)

### Usage
After executing main.py, the script will waiting for user input

Provide input file path => expect csv file path : str

<img width="598" alt="image" src="https://user-images.githubusercontent.com/53313373/228105820-61a5d40c-b79d-448e-8651-f0ce9b7b59ba.png">

Provide output path => expect folder path :str

<img width="598" alt="image" src="https://user-images.githubusercontent.com/53313373/228106054-bb9a7692-0825-4d2e-b689-0ce8ee41a09b.png">

Provide delta => expect float (default value is None => Try to find perfect match between latitude and longitude values)

Get all rows from temp_result_data with values for lat and long in range:
lat +- delta ; long +- delta

```
Example:
if the current latitude   = 42.000000,
and the current longitude = 23.000000
and the delta value       = 0.005
-------------------------------------
The script will get all rows with 
latitude in range (41.995 to 42.005) and longitude in range(22.995 to 23.005) 
```

<img width="598" alt="image" src="https://user-images.githubusercontent.com/53313373/228106379-60052597-2720-465b-aaf7-338719eee714.png">


### Logic

The script will perform the following steps:

1. Validate the input file path
2. Create output directory if not exists.
3. Validate the delta value
4. Read the input CSV file and extract the addresses.
5. For every address Convert any Cyrillic characters in the address to Latin characters.
6. Send a request to the Geoapify API to retrieve the latitude and longitude values for each address.
7. Compare the retrieved latitude and longitude values with the latitude and longitude values in other rows,
and filter all names with same address.
8. Sort the result
9. Write the filtered data to a new CSV file in the specified output directory.

By default, the script will not print any output to the console. However, you can enable verbose mode by setting the verbose attribute of the GroupPeople instance to True.

### Parameters
The GroupPeople class constructor takes the following parameters:

geoapify_key: Your Geoapify API key.

input_file: The path to the input CSV file.

output_dir: The path to the output directory where the filtered CSV file will be saved.

delta (optional): The maximum difference allowed between the retrieved latitude and longitude values and the values from the input CSV file. The default value is None, which means no filtering will be performed.

verbose (optional): Whether to print verbose output to the console. The default value is False.

License
This script is licensed under the MIT License.
