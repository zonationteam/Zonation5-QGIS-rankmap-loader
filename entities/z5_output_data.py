import pandas as pd

class Z5OutputData:
    def __init__(self, outputfolder_path: str) -> None:
        self.summary_data = None
        self.feature_data = None
        self.set_output_folder(outputfolder_path)

    def __str__(self) -> str:
        sum_data_line = f"Summary data:\n{str(self.summary_data.head(2))}"
        feat_data_line = f"Feature data:\n{str(self.feature_data.head(2))}"
        return f"{sum_data_line},\n{feat_data_line}\n"

    def set_output_folder(self, outputfolder_path: str) -> None:
        self.summary_data = pd.read_csv(
            f"{outputfolder_path}/summary_curves.csv",
            sep=' '
        )
        self.feature_data = pd.read_csv(
            f"{outputfolder_path}/feature_curves.csv",
            sep=' '
        ).iloc[:, :-1] # Because this file contains whitespaces at the end of each row
