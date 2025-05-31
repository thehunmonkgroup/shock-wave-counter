"""Handles database operations for the shock wave counter."""

import sqlite3
from datetime import datetime
from pathlib import Path


class Database:
    """
    Manages interactions with the SQLite database for storing shock wave strike data.
    """

    def __init__(self, db_path: str | Path) -> None:
        """
        Initializes the Database object and ensures the database and table exist.

        :param db_path: The path to the SQLite database file.
        :type db_path: Union[str, Path]
        """
        self.db_path: Path = Path(db_path)
        self._initialize_db()

    def _initialize_db(self) -> None:
        """
        Creates the database directory and the strike_log table if they don't exist.
        """
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS strike_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strikes_count INTEGER NOT NULL,
                entry_datetime TEXT NOT NULL,
                tag TEXT
            )
            """
        )
        conn.commit()
        conn.close()

    def add_strike_entry(
        self, strikes_count: int, entry_datetime: datetime, tag: str | None = None
    ) -> None:
        """
        Adds a new strike entry to the database.

        :param strikes_count: The number of strikes for this entry.
        :type strikes_count: int
        :param entry_datetime: The date and time of the entry.
        :type entry_datetime: datetime
        :param tag: An optional tag for the entry, defaults to None.
        :type tag: str | None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO strike_log (strikes_count, entry_datetime, tag) VALUES (?, ?, ?)",
            (strikes_count, entry_datetime.isoformat(), tag),
        )
        conn.commit()
        conn.close()

    def get_total_strikes(self, tag: str | None = None) -> int:
        """
        Calculates the total number of strikes, optionally filtered by a tag.

        The tag comparison is case-insensitive.

        :param tag: An optional tag to filter the strikes by, defaults to None.
        :type tag: str | None
        :return: The total number of strikes.
        :rtype: int
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query = "SELECT SUM(strikes_count) FROM strike_log"
        params = []

        if tag:
            query += " WHERE LOWER(tag) = ?"
            params.append(tag.lower())

        cursor.execute(query, params)
        result = cursor.fetchone()[0]
        conn.close()
        return result if result is not None else 0

    def get_summary_by_tag(self) -> tuple[dict[str | None, int], int]:
        """
        Calculates the sum of strikes for each tag and the grand total.

        Tags are returned as stored (which should be lowercase).
        Entries with no tag are grouped under a `None` key.

        :return: A tuple containing:
                 - A dictionary mapping tags (str or None) to their total strikes (int).
                 - The grand total of all strikes (int).
        :rtype: tuple[dict[str | None, int], int]
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query_tags = """
            SELECT tag, SUM(strikes_count)
            FROM strike_log
            GROUP BY tag
            ORDER BY tag
        """
        cursor.execute(query_tags)
        tag_summaries: dict[str | None, int] = {}
        grand_total = 0
        for row in cursor.fetchall():
            tag, count = row
            tag_summaries[tag] = count
            grand_total += count

        conn.close()
        return tag_summaries, grand_total

    def get_strike_details(
        self, tag: str | None = None
    ) -> list[tuple[str | None, str, int]]:
        """
        Retrieves detailed strike entries, optionally filtered by a tag.

        Entries are sorted by tag (case-insensitive, 'Untagged' effectively first
        due to NULL sorting) and then by entry_datetime in descending order.

        :param tag: An optional tag to filter the strikes by (case-insensitive).
        :type tag: str | None
        :return: A list of tuples, where each tuple contains:
                 (tag_name or None, entry_datetime_iso_string, strikes_count).
        :rtype: list[tuple[str | None, str, int]]
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        params = []
        query = """
            SELECT tag, entry_datetime, strikes_count
            FROM strike_log
        """

        if tag:
            query += " WHERE LOWER(tag) = ?"
            params.append(tag.lower())

        query += " ORDER BY LOWER(tag) ASC, entry_datetime DESC"

        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        return results
