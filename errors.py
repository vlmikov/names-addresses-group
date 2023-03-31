class FileCsvNotFoundError(Exception):
    """
    Exception raised for errors in case of providing wrong path:
    Attributes:
        message -- explanation of the error
    """

    def __int__(self, message):
        self.message = message
        super().__init__(self.message)


class InputFileHeaderNotValid(Exception):
    """
    Exception raised in case of wrong input file header
    Attributes:
        message -- explanation of the error
    """

    def __int__(self, message):
        self.message = message
        super().__init__(self.message)
