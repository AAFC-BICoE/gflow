class Input:
    """
    Custom object for mapping dataset names, labels, and input types together.

    Args:
        input_type (str): Whether the data is being imported from a local file, URL, or the Galaxy FS
        name (str): The location or URL of the dataset being imported
        label (str): The input label for that step in the workflow

    """
    def __init__(self, input_type, name, label):
        self.input_type = input_type
        self.name = name
        self.label = label
