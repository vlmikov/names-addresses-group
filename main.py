import builtins
import pandas as pd
import re
import requests
from fuzzywuzzy import fuzz
import os
from datetime import datetime
import pathlib
from errors import FileCsvNotFoundError, InputFileHeaderNotValid
from constants import (
    API_KEY,
    expected_header,
    data_street_main,
    translit_dict,
    verbose,
    similarity_score_threshold,
)


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
        self.geocode_api = None
        self.go_preprocessing_address = None

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
            self.verbose_print("Input file path is not valid!")
        # If file path is file check if the extension is valid
        else:
            self.verbose_print("Check the extension of input file!")
            input_file_extension = pathlib.Path(self.input_file).suffix
            if input_file_extension != ".csv":
                res_file = 422
                self.verbose_print("Wrong file format! Please provide csv file!")
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
            self.verbose_print("Wrong directory")
            res_output_dir = 500

        if res_output_dir == 200 and res_file == 200:
            return 200
        else:
            return 500

    @staticmethod
    def basic_preprocess_df(data):
        """
        This method make preprocessing over input dataframe
        - Remove duplicate
        - Drop rows with missing values
        :param:   data =>  pd.DataFrame
        :return:  data =>  pd.DataFrame
        """
        # Remove duplicate
        data.drop_duplicates(inplace=True)
        # Drop rows with missing values
        data.dropna(inplace=True)
        return data

    @staticmethod
    def has_cyrillic(text: str) -> bool:
        """
        This method check if provided string has cyrillic
        :param text:  str => address string
        :return:     bool => True if cyrillic char found
        """
        has_cyrillic = bool(re.search("[а-яА-Я]", text))

        return has_cyrillic

    @staticmethod
    def cyrillic_to_latin(address: str) -> str:
        """
        This static method convert cyrillic string to latin
        :param address:  str => The address with cyrillic
        :return:         str => converted string
        """
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
        print(f"address request to the api =>>  {address}")
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
        """
        This method validates the header of the input file. Expected header in constants.py
        :param data: pandas.DataFrame => Input data
        :return:                 bool => True or raise InputFileHeaderNotValid error
        """
        # get data header as list
        columns = data.columns.to_list()
        # compare data header with expected header
        if columns != expected_header:
            raise InputFileHeaderNotValid(
                "The header of the input file is not valid! "
                "Check expected header in constants.py"
            )
        return True

    @staticmethod
    def log_error_address(message: str) -> None:
        """
        This method accepts error message and log the error in failed.txt file
        :param message: str => message
        :return:        None
        """
        file = open("failed.txt", "a")
        file.write(str(message))
        file.close()

    def data_street_fill(self, street_section: str, street_data) -> object:
        """
        This method accepts street_section and street data from constants.py
        Try to find match with some groups in data_street_main from constants.py
        :param street_section:
        :param street_data:
        :return:
        """
        # Get data street from constats.py dict
        data_street = street_data["data"]
        # Check if street section from the address has cyrillic characters
        has_cyr = self.has_cyrillic(street_section)
        if has_cyr:
            # Transliterate the street section
            street_section = self.cyrillic_to_latin(street_section)

        # Loop over all data_street
        for type_ in data_street:
            # Loop over all elements in current list
            for sub_type in type_:
                # Check if some str is in street_section
                if sub_type in street_section:
                    # If the street section has cyrillic letters
                    if has_cyr:
                        # replace the match string with the second element from current list
                        street_section = street_section.replace(
                            sub_type, type_[1].strip()
                        )
                        # Change the position of the element in the strung
                        street_section = street_section.replace(
                            type_[1].strip(), ""
                        ).strip()
                        street_section = f"{type_[1].strip()} {street_section}"
                        # street_section = self.cyrillic_to_latin(street_section)
                        break
                    # If the street section doesn't have any cyrillic letter
                    else:
                        # Check if the index of matched string in current list is 1
                        if type_.index(sub_type) == 1:
                            street_section = street_section.replace(
                                sub_type, type_[1].strip()
                            )
                            street_section = street_section.replace(
                                type_[1], ""
                            ).strip()
                            street_section = f"{type_[1].strip()} {street_section}"
                            break
                        # If the index is not 1 set the sting as first element in the current list
                        else:
                            street_section = street_section.replace(
                                sub_type, type_[0].strip()
                            )
                            street_section = street_section.replace(
                                type_[0].strip(), ""
                            ).strip()
                            street_section = f"{type_[0].strip()} {street_section}"
                            break

        return street_section

    def preprocess_street(self, street_section):
        """
        This method preprocess street section string from address string
        - Change the position of the number in the end of the street_section
        - Check if in the street_section has any key-words from data_street_main in constants.py
        :param   street_section:   str => street_section
        :return: street_section    str => modified street_section
        """
        street_section = street_section.strip()
        # Extract number street
        number_regex = r"\d+"
        number_street = re.search(number_regex, street_section)
        number_street = number_street.group()
        # Change the position of the number always in the end of the street section
        street_section = street_section.replace(number_street, "").strip()
        street_section = f"{street_section.strip()} {number_street.strip()}"
        # Check if in the street_section has any key-words from data_street_main in constants.py
        street_section = self.data_street_fill(street_section, data_street_main)
        return street_section

    def preprocess_section(self, section):
        """
        This method accept country or city section
        - Put post code or country code in the end of the section
        :param section:  str => section
        :return:         str => Modified section
        """
        section = section.strip()
        number_regex = r"\d+"
        if self.has_cyrillic(section):
            section = self.cyrillic_to_latin(section)
        # Find postcode or country code in section
        post_code = re.search(number_regex, section)
        # Put post code or country code in the end of the section
        if post_code:
            post_code = post_code.group()
            section = section.replace(post_code, "").strip()
            section = f"{section} {post_code}"
        return section

    def address_preprocess(self, address):
        """
        This method accept string address and extract all possible sections and preprocess every section
        :param address:  str => address
        :return:         str => Modified address
        """
        address_res = []
        try:
            street_section = address.split(", ")[0]
            street_section = self.preprocess_street(street_section)
            # print(f'STREEETT {street_section}')
            address_res.append(street_section)
        except (Exception,):
            pass

        # Get city
        try:
            city_section = address.split(", ")[1]
            city_section = self.preprocess_section(city_section)
            address_res.append(city_section)
        except (Exception,):
            pass

        try:
            # Get country
            country_section = address.split(", ")[2]
            country_section = self.preprocess_section(country_section)
            address_res.append(country_section)
        except (Exception,):
            pass

        try:
            add_section = address.split(", ")[3]
            address_res.append(add_section)

        except (Exception,):
            pass

        # address = f"{street_section}, {city_section}, {country_section}, {add_section}"
        address = ", ".join(address_res)

        return address

    def get_coor_main(self, address):
        """
        This method accepts addreess as string and :
        - Check if address is not empty string or None
        - Process the address if self.go_preprocessing_address is True
        - Transliterate address if cyrillic -> cyrillic to latin
        - get coordinates for the address -> geocode API request if self.geocode_api is True
        :param address:   str => address
        :return:          lat    :  float => latitude
                          long   :  float => longitude
                          address:  str
                          message:  str
        """
        # Check if address is None or empty string
        if not address or address == "":
            return None, None, None, None
        # Convert address to lowercase letter
        address = address.lower()
        # Check if the address contains cyrillic letters

        # preprocess address
        if self.go_preprocessing_address:
            address = self.address_preprocess(address)
        else:
            if self.has_cyrillic(address):
                address = self.cyrillic_to_latin(address)
        # Get coordinates latitude and longitude for current address
        if self.geocode_api:
            lat, long, mess = self.get_coordinates(address)
            print(f"Type latitude : {type(lat)}")
        else:
            lat, long, mess = "", "", ""
            mess = "OK"
        if mess != "OK":
            error_message = mess
            to_log = f"Error in getting coordinates for address '{address}' => message {error_message} \n"
            self.log_error_address(to_log)
            return "", "", address, error_message
        return lat, long, address, ""

    @staticmethod
    def process_data(row, data):
        """
        This method accepts row with latitude and longitude range and input dataframe
        - Get the latitude and longitude range for the current row
        - Filter the data based on the lat-long range
        - Sort the filtered data by Name column
        - Get names from the filtered data
        - Join the list of names as string with separator ', '
        - Create a new row for the results DataFrame
        - Return the new row
        :param row:
        :param data:
        :return:
        """
        print(type(row))
        # Get the latitude and longitude range for the current row
        latitude_range = (row["lat_min"], row["lat_max"])
        longitude_range = (row["long_min"], row["long_max"])

        # Filter the data based on the lat-long range
        sub_data = data[
            (data["lat"].between(*latitude_range))
            & (data["long"].between(*longitude_range))
        ]
        # Sort the filtered data by Name column
        sub_data = sub_data.sort_values(by=["Name"])
        # Get the names from the filtered data
        names = sub_data["Name"]
        # Join the names as a string
        str_names = ", ".join(names)

        # Create a new row for the results DataFrame
        return {
            "GroupedNames": str_names,
            "lat": row["lat_min"],
            "long": row["long_min"],
        }

    def get_path_output_file(self):
        """
        This method create output path for the result file
        :return:  string => full path for result file
        """
        # Get time now
        now = datetime.now()
        # Create unique string
        dt_string = now.strftime("%d_%m_%Y__%H_%M_%S")
        # The name of output file always is unique using dt_string
        res_file_name = f"file_{dt_string}.csv"
        self.verbose_print(f"Create output filename => {res_file_name}")
        # Concat the output dir with file name
        res_path = os.path.join(self.output_dir, res_file_name)
        self.verbose_print(f"Create output file path => {res_path}")
        return res_path

    @staticmethod
    def calc_similarity(address_1, address_2):
        """
        This method accepts 2 addresses and return integer value between 0 and 100
        100 means exact match
        :param address_1: str
        :param address_2: str
        :return: int
        """
        return fuzz.ratio(address_1, address_2)

    def fuzzy_compare(self, data):
        """
        This method accepts pandas dataframe:
        - Calculates the pairwise similarity scores between all addresses
        - Converts the pairwise similarity scores into a new DataFrame with two columns
        - Groups the similar addresses and get the corresponding names using similarity_score_threshold
          from constants.py
        - Using grouped_addresses extracts group_names
        - Create a DataFrame with the concat grouped names by ', '
        -
        :param   data:  pandas DataFrame
        :return: data:  pandas DataFrame
        """
        # Calculate the pairwise similarity scores between all addresses
        similarity_scores = data["Address"].apply(
            lambda address1: data["Address"].apply(
                lambda address2: self.calc_similarity(address1, address2)
            )
        )
        # Convert the pairwise similarity scores into a new DataFrame with two columns
        similarity_df = similarity_scores.stack().reset_index()
        similarity_df.columns = ["Address1", "Address2", "SimilarityScore"]
        similarity_df = similarity_df[
            similarity_df["Address1"] != similarity_df["Address2"]
        ]
        # Group the similar addresses and get the corresponding names using similarity_score_threshold from constants.py
        grouped_addresses = []
        for address in similarity_df["Address1"].unique():
            similar_addresses = similarity_df[
                (similarity_df["Address1"] == address)
                & (similarity_df["SimilarityScore"] > similarity_score_threshold)
            ]["Address2"].tolist()
            # Append to the current similar_addresses result df current value in Address1 column in similarity_df
            similar_addresses.append(address)
            # Sort the result
            similar_addresses = sorted(similar_addresses)
            # Add similar_addresses to the grouped_addresses list if still not there
            if similar_addresses not in grouped_addresses:
                grouped_addresses.append(similar_addresses)

        # Using grouped_addresses extract group_names
        grouped_names = []
        for group in grouped_addresses:
            names = [data.iloc[index]["Name"] for index in group]
            names = sorted(names)
            grouped_names.append(names)

        # Create a DataFrame with the concat grouped names by ', '
        result = [", ".join(names) for names in grouped_names]
        # Create dataframe from grouped_name list with column name GroupedNames
        df = pd.DataFrame(result, columns=["GroupedNames"])
        # Sort dataframe Alphabetically
        df = df.sort_values(by="GroupedNames")
        return df

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
        # Preprocess dataframe
        data = self.basic_preprocess_df(data)
        # Loop over every row in input data
        self.verbose_print(
            "Apply get_coor_main method logic over all addresses in column Address",
            "Create new columns lat, long , mess and fill it ",
        )
        data[["lat", "long", "Address", "mes"]] = data["Address"].apply(
            lambda x: pd.Series(self.get_coor_main(x))
        )
        # Check if geocode_api is False
        if not self.geocode_api:
            self.verbose_print("-" * 100, "Prepare result file")
            # Make a fuzzy compare between all addresses
            temp_result = self.fuzzy_compare(data)
        # If geocode_api is True
        else:
            # Get unique lat-long pairs from the data
            # Check if delta is provided
            if self.delta is not None:
                # Create dataframe with latitude and longitude change depends on delta value
                delta_data = pd.DataFrame(
                    {
                        "lat_min": data["lat"] - self.delta,
                        "lat_max": data["lat"] + self.delta,
                        "long_min": data["long"] - self.delta,
                        "long_max": data["long"] + self.delta,
                    }
                )
                # Apply the function to each row of delta_data and concatenate the results into a DataFrame
                temp_result = pd.DataFrame(
                    delta_data.apply(self.process_data, axis=1, data=data).tolist()
                )
                temp_result.drop(["lat", "long"], axis=1, inplace=True)
                temp_result.drop_duplicates(inplace=True)
                temp_result = temp_result.sort_values(by="GroupedNames")
            else:
                temp_result = []
                # Loop over data
                for index, row in data.iterrows():
                    # Get current latitude and longitude
                    lat = row["lat"]
                    long = row["long"]
                    # Get all rows from temp_result_data with values for lat and long same as current lat and long:
                    sub_res = data[(data["lat"] == lat) & (data["long"] == long)]
                    # Get all values in column Name from filtered dataframe
                    col_data = sub_res["Name"]
                    # Sort values in list result
                    col_data = sorted(col_data)
                    # Join the list values as string with separator ", "
                    col_data = ", ".join(col_data)
                    # Append the result if not there
                    if [col_data] not in temp_result:
                        temp_result.append([col_data])

                temp_result = pd.DataFrame(temp_result, columns=["GroupedNames"])
                temp_result = temp_result.sort_values(by="GroupedNames")

        # Get time now as string in order to generate unique files without overwrite existing one
        res_path = self.get_path_output_file()
        # Save the result dataframe in csv file
        temp_result.columns = [None] * len(temp_result.columns)
        # temp_result = temp_result.rename(columns=lambda x: x.strip())
        temp_result.to_csv(res_path, index=False)
        self.verbose_print(f"Result file {res_path} crated successful!")


if __name__ == "__main__":
    group_people = None
    print("GroupPeople class Variant 1 => Version: 0.0.1 ")
    while True:
        print("-" * 50)
        input_file_ = input("Input file (Required .csv files): ")
        result_dir_ = input("Output dir (Format => 'dir/dir_1' or 'dir/dir_1/'): ")
        delta_ = input("Delta (value float)(default is None): ")

        # input_file_ = 'ResTecDevTask-sample_input_v1.csv'
        # result_dir_ = 'result/'
        # delta_ = 0.0004
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
        while True:
            geocode_api = input(
                f"Do you want to use geocod api https://www.geoapify.com/ (y, n): "
            ).lower()
            if geocode_api not in ["y", "n"]:
                print('Wrong choice: Possible options ["y", "n"]')
                continue
            if geocode_api == "y":
                group_people.geocode_api = True
                group_people.go_preprocessing_address = False
            else:
                group_people.geocode_api = False
                group_people.go_preprocessing_address = True
            break
        # Set verbose
        group_people.verbose = verbose
        # Validate input
        res_val = group_people.validate_input()
        if res_val == 200:
            break
        else:
            print("Error in validating input file or output directory!")
    group_people.process_file()
    print("The script finished successfully!")
