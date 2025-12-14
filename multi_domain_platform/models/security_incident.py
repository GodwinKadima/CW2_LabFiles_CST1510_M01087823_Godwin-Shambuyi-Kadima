class SecurityIncident:
    """Represents a cybersecurity incident in the platform."""
    def __init__(self, incident_id: int, incident_type: str, severity: str, status: str, description: str):
        self.__id = incident_id
        self.__incident_type = incident_type
        self.__severity = severity
        self.__status = status
        self.__description = description

    def get_id(self) -> int:
        return self.__id

    def get_status(self) -> str:
        return self.__status

    def get_description(self) -> str:
        return self.__description

    def get_severity_level(self) -> int:
        """Return an integer severity level (simple example)."""
        mapping = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4,
        }
        return mapping.get(self.__severity.lower(), 0)

    def __str__(self) -> str:
        return f"Incident {self.__id} [{self.__severity.upper()}] {self.__incident_type}"
