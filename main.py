import builtins
import pandas as pd
import re
import requests
from constants import API_KEY, expected_header
import os
from datetime import datetime
import pathlib
from errors import FileCsvNotFoundError


# https://www.geoapify.com/
class GroupPeople:
    def __init__(
        self, geoapify_key: str, input_file: str, output_dir: str, delta: float = None
    ):
        self.geoapify_key = geoapify_key
        self.input_file = input_file
        self.output_dir = output_dir
        self.delta = delta
        self.verbose = False

    def verbose_print(self, *args) -> None:
        """
        :param args: Accepts string args
        :return:     If verbose is True prints all strings in new line.
        """
        if self.verbose is True:
            builtins.print(*args, sep="\n")

    def validate_input(self) -> int:
        """
        This method validate the input file path and output directory
        :return: int => 200 (in case of valid input) or 500 (in case of invalid input)
        """
        self.verbose_print(
            "=" * 100,
            "Validate input file",
            "-" * 100,
            "Check if input file path is file",
        )
        # Check if input file path is a file
        is_file = os.path.isfile(self.input_file)
        if not is_file:
            res_file = 404
            print("Input file path is not valid!")
        # If file path is file check if the extension is valid
        else:
            self.verbose_print("Check the extension of input file!")
            input_file_extension = pathlib.Path(self.input_file).suffix
            if input_file_extension != ".csv":
                res_file = 422
                print("Wrong file format! Please provide csv file!")
            else:
                res_file = 200
                self.verbose_print("Expecting input file extension is correct.")

        # Validate output dir.
        self.verbose_print("-" * 100, "Validate output dir")
        try:
            # Check if the output dir is exists.
            if not os.path.exists(self.output_dir):
                # Create folder tree
                os.makedirs(self.output_dir)
                self.verbose_print("Output folder has been created.")
            # In case of successfully created output folder set res_output_dir to 200
            res_output_dir = 200
        except (Exception,):
            # If the output directory is not created set res_output_dir ot 500
            print("Wrong directory")
            res_output_dir = 500

        if res_output_dir == 200 and res_file == 200:
            return 200
        else:
            return 500

    @staticmethod
    def has_cyrillic(text: str) -> bool:
        """
        This method check if provided string has cyrillic
        :param text:  str => address string
        :return:     bool => True if cyrillic char found
        """
        return bool(re.search("[а-яА-Я]", text))

    @staticmethod
    def cyrillic_to_latin(address: str) -> str:
        """
        This static method convert cyrillic string to latin
        :param address:  str => The address with cyrillic
        :return:         str => converted string
        """
        # Define the Cyrillic to Latin transliteration dictionary
        translit_dict = {
            "а": "a",
            "б": "b",
            "в": "v",
            "г": "g",
            "д": "d",
            "е": "e",
            "ж": "zh",
            "з": "z",
            "и": "i",
            "к": "k",
            "л": "l",
            "м": "m",
            "н": "n",
            "о": "o",
            "п": "p",
            "р": "r",
            "с": "s",
            "т": "t",
            "у": "u",
            "ф": "f",
            "х": "h",
            "ц": "c",
            "ч": "ch",
            "ш": "sh",
            "щ": "sht",
            "ъ": "u",
            "ю": "yu",
            "я": "a",
        }

        """
        Converts Cyrillic text to Latin using standard transliteration rules.
        """
        lat_text = ""
        for char in address:
            if char in translit_dict:
                lat_text += translit_dict[char]
            else:
                lat_text += char
        return lat_text

    @staticmethod
    def get_coordinates(address: str) -> (str, str):
        """
        This static method get coordinates (latitude, longitude) of given address
        :param address:         str => The address string
        :return:       float, float => latitude, longitude
        """

        # Build the API URL
        url = f"https://api.geoapify.com/v1/geocode/search?text={address}&limit=1&apiKey={API_KEY}"

        try:
            # Send the API request and get the response
            response = requests.get(url)
        except (Exception,):
            error_str = f'Requested address: "{address}" failed'
            return None, None, error_str

        # Check the response status code
        if response.status_code == 200:
            # Parse the JSON data from the response
            data = response.json()

            # Extract the first result from the data
            result = data["features"][0]

            # Extract the latitude and longitude of the result
            latitude = result["geometry"]["coordinates"][1]
            longitude = result["geometry"]["coordinates"][0]
            success_message = "OK"
            return latitude, longitude, success_message
        else:
            error_str = f"Request failed with status code {response.status_code}"
            print(error_str)

            return None, None, error_str

    @staticmethod
    def validate_header(data):
        # get header
        columns = data.columns.to_list()
        if columns != expected_header:
            raise Exception
        return True

    @staticmethod
    def log_error_address(message):
        file = open("faild.txt", "a")
        file.write(str(message))
        file.close()

    def process_file(self):
        """
        This method process the input file and generate the result
        :return:
        """
        self.verbose_print("-" * 100, "Start processing file", "Open input file")
        # Open input file
        try:
            data = pd.read_csv(self.input_file)
            self.verbose_print("")
        except:
            raise FileCsvNotFoundError("Error in opening file")
        # validate header of input file with expected columns in constants.py
        self.verbose_print("Validate input file header")
        self.validate_header(data)
        temp_result = []
        # Loop over every row in input data
        self.verbose_print("Loop over data, process every address and get coordinates")
        for index, row in data.iterrows():
            # get the Address for current row
            address_ = row.get("Address")
            # Check if address is None or empty string
            if address_ is None or address_ == "":
                continue
            # Convert address to lowercase letter
            address_ = str(address_).lower()
            # Check if the address contains cyrillic letters
            if self.has_cyrillic(address_):
                # convert cyrillic address to latin
                address_ = self.cyrillic_to_latin(address_)
            # Get coordinates latitude and longitude for current address
            lat, long, mess = self.get_coordinates(address_)
            if mess != "OK":
                error_message = mess
                to_log = (
                    f"Error in getting coordinates for index {index} "
                    f"with address '{address_}' => message {error_message} \n"
                )
                self.log_error_address(to_log)
                continue
            # create new columns with name lat and long and set current latitude and longitude for.
            row["lat"] = lat
            row["long"] = long
            # Add the row to the temp result
            temp_result.append(row)

        """
        Create dataframe from temp result list of dicts
        The shape of temp result is the same as the input file with additional two columns "lat" and "long"
        """
        res_data = pd.DataFrame(temp_result)

        temp_result = []
        # Loop over temp_result_data
        self.verbose_print("-" * 100, "Prepare result file")
        for i, r in res_data.iterrows():
            # Get latitude and longitude
            lat = r.get("lat")
            long = r.get("long")
            # Check if delta provided
            if self.delta is not None:
                try:
                    # Create Dataframe from temp_result list of dicts
                    curr_res = pd.DataFrame(temp_result)
                    """
                    Get all rows from temp_result_data with values for lat and long in range:
                    lat +- delta ; long +- delta
                    """
                    sub_res = curr_res[
                        (
                            (curr_res["lat"] - self.delta < lat)
                            & (curr_res["lat"] + self.delta > lat)
                        )
                        & (
                            (curr_res["long"] - self.delta < long)
                            & (curr_res["long"] + self.delta > long)
                        )
                    ]
                    # Check if the current address is processed
                    if len(sub_res) > 0:
                        continue
                except (Exception,):
                    pass
                """ 
                Get all rows from temp_result_data with values for lat and long in range:
                lat +- delta ; long +- delta
                Example:
                if the current latitude   = 42.000000,
                and the current longitude = 23.000000
                and the delta value       = 0.005
                -------------------------------------
                The script will get all rows with 
                latitude in range (41.995 to 42.005) and longitude in range(22.995 to 23.005) 
                """
                sub_data = res_data[
                    (
                        (res_data["lat"] - self.delta < lat)
                        & (res_data["lat"] + self.delta > lat)
                    )
                    & (
                        (res_data["long"] - self.delta < long)
                        & (res_data["long"] + self.delta > long)
                    )
                ]
            # If delta not provided
            else:
                try:
                    curr_res = pd.DataFrame(temp_result)
                    # Get all rows from temp_result_data with values for lat and long same as current lat and long:
                    sub_res = curr_res[
                        (curr_res["lat"] == lat) & (curr_res["long"] == long)
                    ]
                    # Check if the current address is processed
                    if len(sub_res) > 0:
                        continue
                except (Exception,):
                    pass
                # Get all rows from temp_result_data with values for lat and long same as current lat and long:
                sub_data = res_data[
                    (res_data["lat"] == lat) & (res_data["long"] == long)
                ]

            # sort sub_data by column Name
            sub_data = sub_data.sort_values(by=["Name"])
            # get all names from sub_data in column 'Name'
            names = sub_data["Name"]
            # join the list as string with separator ', '
            str_names = ", ".join(names)
            """
            Create shape of temp result row with lat and long as columns
            in order to compare if address is already processed
            """
            r = {"Names_with_same_address": str_names, "lat": lat, "long": long}
            # Add current row to temp_result list
            temp_result.append(r)

        # Convert temp_result list to Dataframe
        d_res = pd.DataFrame(temp_result)
        # Remove 'lat' column because we don't need it
        d_res = d_res.drop("lat", axis=1)
        # Remove 'long' column
        d_res = d_res.drop("long", axis=1)
        # Sort dataframe by Names_with_same_address
        d_res = d_res.sort_values(by="Names_with_same_address")
        # Get time now as string in order to generate unique files without overwrite existing one
        now = datetime.now()
        dt_string = now.strftime("%d_%m_%Y__%H_%M_%S")
        # The name of output file always is unique using dt_string
        res_file_name = f"file_{dt_string}.csv"
        self.verbose_print(f"Create output filename => {res_file_name}")
        # Concat the output dir with file name
        res_path = os.path.join(self.output_dir, res_file_name)
        self.verbose_print(f"Create output file path => {res_path}")
        # Save the result dataframe in csv file
        d_res.to_csv(res_path, index=False)
        self.verbose_print(f"Result file {res_path} crated successful!")


if __name__ == "__main__":
    group_people = None
    print("GroupPeople class Variant 1 => Version: 0.0.1 ")
    while True:
        print("-" * 50)
        input_file_ = input("Input file (Required .csv files): ")
        result_dir_ = input("Output dir (Format => 'dir/dir_1' or 'dir/dir_1/'): ")
        delta_ = input("Delta (value float)(default is None): ")
        if delta_ == "":
            delta_ = None
        else:
            try:
                delta_ = float(delta_)
            except (Exception,):
                print("Wrong delta value! Expected float")
                continue
        group_people = GroupPeople(
            geoapify_key=API_KEY,  # API_KEY from https://www.geoapify.com/ => get from constants.py
            input_file=input_file_,  # input_file from user input
            output_dir=result_dir_,  # output dir from user input
            delta=delta_,  # delta value for define a range for match
        )
        # Set verbose to True
        group_people.verbose = True
        # Validate input
        res_val = group_people.validate_input()
        if res_val == 200:
            break
    group_people.process_file()
    print("The script finished successfully!")
