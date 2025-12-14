from typing import Optional

class Dataset:
    """
    Represents a data science dataset stored in the database.

    Attributes:
        id (Optional[int]): The unique primary key ID of the dataset.
        name (str): The name or title of the dataset.
        size_bytes (int): The size of the file in bytes.
        rows (int): The number of rows (records) in the dataset.
        source (str): The origin or source of the dataset (e.g., Kaggle, internal).
        status (str): The processing status of the dataset (e.g., 'Pending', 'Ready', 'In Use').
        reported_by (str): The username or ID of the user who reported/uploaded the dataset.
    """
    
    # Default status when a new dataset is created
    DEFAULT_STATUS = "Pending" 

    def __init__(
        self,
        name: str,
        size_bytes: int,
        rows: int,
        source: str,
        reported_by: str,
        status: str = DEFAULT_STATUS,
        dataset_id: Optional[int] = None,
    ):
        """
        Initializes a Dataset object.
        """
        self._id = dataset_id
        self._name = name
        self._size_bytes = size_bytes
        self._rows = rows
        self._source = source
        self._status = status
        self._reported_by = reported_by

    # --- Getters ---

    def get_id(self) -> Optional[int]:
        """Returns the dataset's unique ID."""
        return self._id

    def get_name(self) -> str:
        """Returns the dataset name."""
        return self._name

    def get_rows(self) -> int:
        """Returns the number of rows in the dataset."""
        return self._rows

    def get_source(self) -> str:
        """Returns the source of the dataset."""
        return self._source
    
    def get_status(self) -> str:
        """Returns the current status of the dataset."""
        return self._status

    def get_reported_by(self) -> str:
        """Returns the user who reported the dataset."""
        return self._reported_by

    # --- Setters ---

    def set_status(self, new_status: str) -> None:
        """Sets a new processing status for the dataset."""
        self._status = new_status
        
    # --- Utility Methods ---

    def format_size(self) -> str:
        """Formats the size_bytes into a human-readable string (KB, MB, GB)."""
        size = self._size_bytes
        if size < 1024:
            return f"{size} bytes"
        elif size < 1024**2:
            return f"{size / 1024:.2f} KB"
        elif size < 1024**3:
            return f"{size / 1024**2:.2f} MB"
        else:
            return f"{size / 1024**3:.2f} GB"

    def __str__(self) -> str:
        """Provides a user-friendly string representation for debugging and logging."""
        return (
            f"Dataset(ID={self._id}, Name='{self._name}', Rows={self._rows}, "
            f"Size={self.format_size()}, Source='{self._source}', Status='{self._status}')"
        )

# Example Usage (for testing/demonstration, remove in final file)
if __name__ == '__main__':
    example_dataset = Dataset(
        name="Cyber Attack Logs 2024",
        size_bytes=5242880, # 5 MB
        rows=150000,
        source="Internal SOC System",
        reported_by="data_analyst_01",
        dataset_id=1
    )
    print(example_dataset)
    example_dataset.set_status("Ready")
    print(f"New Status: {example_dataset.get_status()}")
    print(f"Formatted Size: {example_dataset.format_size()}")