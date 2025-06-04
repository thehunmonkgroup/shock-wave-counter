"""
Extracorporeal Shock Wave Machine Strike Counter.

This application allows users to track the total strikes made by a shock wave machine.
It can add new strike counts to an SQLite database or query the total strikes.
"""

import argparse
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import importlib.metadata

from shock_wave_counter import constants
from shock_wave_counter.database import Database
from shock_wave_counter.logger import Logger


class App:
    """
    Core application class for managing shock wave strike counting.

    Encapsulates database interaction and business logic for adding
    and querying strike counts.
    """

    def __init__(self, db_path: Path, logger: logging.Logger) -> None:
        """
        Initializes the App with database and logger.

        :param db_path: Path to the SQLite database file.
        :type db_path: Path
        :param logger: Configured logger instance.
        :type logger: Logger
        """
        self.logger: logging.Logger = logger
        self.logger.debug(f"Initializing Database with path: {db_path}")
        try:
            self.db: Database = Database(db_path)
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
        self.logger.debug("App initialized successfully.")

    def add_strike_entry(self, count_to_add: int, session_tag: str | None) -> None:
        """
        Adds a new strike entry to the database.

        Validates the strike count, processes the tag, and records the entry
        with the current UTC timestamp.

        :param count_to_add: The number of strikes to add (must be positive).
        :type count_to_add: int
        :param session_tag: An optional tag for the session.
        :type session_tag: str | None
        :raises ValueError: If count_to_add is not positive.
        """
        self.logger.debug(
            f"Attempting to add strike entry: count={count_to_add}, tag='{session_tag}'"
        )
        if count_to_add <= 0:
            self.logger.error(
                f"Strike count must be a positive integer, received: {count_to_add}"
            )
            raise ValueError("Strike count must be a positive integer.")

        processed_tag: str | None = None
        if session_tag:
            processed_tag = session_tag.lower()
            self.logger.debug(f"Processed tag: '{processed_tag}'")

        entry_datetime = datetime.now(timezone.utc)
        self.logger.debug(f"Entry datetime (UTC): {entry_datetime.isoformat()}")

        try:
            self.db.add_strike_entry(count_to_add, entry_datetime, processed_tag)
            message = f"Successfully added {count_to_add} strikes." + (
                f" with tag '{processed_tag}'" if processed_tag else ""
            )
            self.logger.debug(message)
            print(message)
        except Exception as e:
            self.logger.error(f"Failed to add strike entry to database: {e}")
            raise

    def query_total_strikes(self, filter_tag: str | None) -> None:
        """
        Queries and prints the total number of strikes, optionally filtered by a tag.

        :param filter_tag: An optional tag to filter the strike count by.
        :type filter_tag: str | None
        """
        self.logger.debug(f"Querying total strikes. Filter tag: '{filter_tag}'")
        processed_filter_tag: str | None = None
        if filter_tag:
            processed_filter_tag = filter_tag.lower()
            self.logger.debug(f"Processed filter tag: '{processed_filter_tag}'")

        try:
            total_strikes = self.db.get_total_strikes(tag=processed_filter_tag)
            self.logger.debug(f"Retrieved total strikes: {total_strikes}")

            if processed_filter_tag:
                if total_strikes > 0:
                    print(
                        f"Total strikes for tag '{processed_filter_tag}': {total_strikes}"
                    )
                else:
                    print(f"No strikes found for tag '{processed_filter_tag}'.")
            else:
                if total_strikes > 0:
                    print(f"Total strikes: {total_strikes}")
                else:
                    print("No strikes recorded yet.")
        except Exception as e:
            self.logger.error(f"Failed to query total strikes from database: {e}")
            raise

    def query_summary(self) -> None:
        """
        Queries and prints a summary of strikes by tag and the grand total.
        """
        self.logger.debug("Querying strike summary.")
        try:
            tag_summaries, grand_total = self.db.get_summary_by_tag()
            self.logger.debug(
                f"Retrieved summary: {len(tag_summaries)} tags, Grand total: {grand_total}"
            )

            if not tag_summaries and grand_total == 0:
                print("No strikes recorded yet.")
                return

            print("Strike Summary:")
            sorted_tags = sorted(tag_summaries.keys(), key=lambda t: (t is None, t))

            for tag in sorted_tags:
                count = tag_summaries[tag]
                if tag is None:
                    print(f"  Untagged: {count} strikes")
                else:
                    print(f"  Tag '{tag}': {count} strikes")

            print("--------------------")
            print(f"Grand Total: {grand_total} strikes")

        except Exception as e:
            self.logger.error(f"Failed to query strike summary from database: {e}")
            raise

    def query_strike_details(
        self, filter_tag: str | None, group_by_date: bool = False
    ) -> None:
        """
        Queries and prints detailed information for each strike entry.

        Allows filtering by a specific tag.
        Can group entries by tag first, then date (default), or by date first, then tag.

        :param filter_tag: An optional tag to filter the detailed entries by.
        :type filter_tag: str | None
        :param group_by_date: If True, group entries by date first, then by tag.
                              Otherwise, group by tag first, then by date.
        :type group_by_date: bool
        """
        self.logger.debug(
            f"Querying strike details. Filter tag: '{filter_tag}', Group by date: {group_by_date}"
        )
        processed_filter_tag: str | None = None
        if filter_tag:
            processed_filter_tag = filter_tag.lower()
            self.logger.debug(
                f"Processed filter tag for details: '{processed_filter_tag}'"
            )

        try:
            entries = self.db.get_strike_details(
                tag=processed_filter_tag, sort_by_date_first=group_by_date
            )
            self.logger.debug(f"Retrieved {len(entries)} strike entries for details.")

            if not entries:
                if processed_filter_tag:
                    print(f"No strike entries found for tag '{processed_filter_tag}'.")
                else:
                    print("No strike entries recorded yet.")
                return

            if group_by_date:
                self.logger.debug(
                    "Displaying strike details grouped by local date, ordered by date (asc) then tag (asc)."
                )
                current_printed_local_date_header: str | None = None
                for db_tag, dt_str, count in entries:
                    dt_obj_utc = datetime.fromisoformat(dt_str)
                    dt_obj_local = dt_obj_utc.astimezone()

                    current_entry_local_date_str_formatted = dt_obj_local.strftime(
                        "%a %b %-d %Y"
                    )

                    if (
                        current_entry_local_date_str_formatted
                        != current_printed_local_date_header
                    ):
                        if current_printed_local_date_header is not None:
                            print()
                        print(f"{current_entry_local_date_str_formatted}:")
                        current_printed_local_date_header = (
                            current_entry_local_date_str_formatted
                        )

                    tag_display = "Untagged" if db_tag is None else f"Tag '{db_tag}'"
                    formatted_time = dt_obj_local.strftime("%-I:%M%p %Z")
                    print(f"  {tag_display}: {formatted_time} - {count} strikes")
            else:
                self.logger.debug("Displaying strike details grouped by tag.")
                entries_by_tag: dict[str, list[dict[str, Any]]] = {}
                for db_tag, dt_str, count in entries:
                    tag_key = db_tag if db_tag is not None else "Untagged"
                    if tag_key not in entries_by_tag:
                        entries_by_tag[tag_key] = []

                    dt_obj = datetime.fromisoformat(dt_str)
                    entries_by_tag[tag_key].append({"datetime": dt_obj, "count": count})

                sorted_tags = sorted(entries_by_tag.keys())

                for i, tag_key in enumerate(sorted_tags):
                    if i > 0:
                        print()

                    if tag_key == "Untagged":
                        print("Untagged Entries:")
                    else:
                        print(f"Details for Tag '{tag_key}':")

                    for entry in entries_by_tag[tag_key]:
                        local_dt = entry["datetime"].astimezone()
                        formatted_dt = local_dt.strftime("%a %b %-d %Y, %-I:%M%p %Z")
                        print(f"  {formatted_dt} - {entry['count']} strikes")

        except Exception as e:
            self.logger.error(f"Failed to query strike details from database: {e}")
            raise

    def display_app_info(self) -> None:
        """
        Displays application information such as version and database path.
        """
        self.logger.debug("Displaying application info.")
        try:
            version = importlib.metadata.version(constants.APP_NAME)
        except importlib.metadata.PackageNotFoundError:
            self.logger.warning(
                f"Could not find package metadata for '{constants.APP_NAME}'. Version will be reported as 'unknown'. This can happen if the package is not installed correctly."
            )
            version = "unknown"

        print(f"{constants.APP_NAME.replace('_', ' ').title()} Information:")
        print(f"  Version: {version}")
        print(f"  Database Path: {self.db.db_path.resolve()}")


def _parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:  # noqa: C901
    """
    Parses command-line arguments for the application.

    :param argv: Optional list of arguments to parse. If None, sys.argv[1:] is used.
    :type argv: list[str] | None
    :return: Namespace object containing parsed arguments.
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        description="Extracorporeal Shock Wave Machine Strike Counter."
    )
    parser.add_argument(
        "-c",
        "--count",
        action="store_true",
        help="Query total strikes instead of adding a new entry.",
    )
    parser.add_argument(
        "-s",
        "--summary",
        action="store_true",
        help="Display a summary of strikes by tag and the grand total.",
    )
    parser.add_argument(
        "-d",
        "--detail",
        action="store_true",
        help="Display detailed strike entries, optionally filtered by --filter-tag.",
    )
    parser.add_argument(
        "-b",
        "--by-date",
        action="store_true",
        help="When used with --detail, group entries by date first, then by tag.",
    )
    parser.add_argument(
        "-i",
        "--info",
        action="store_true",
        help="Display application information (version, database path, etc.).",
    )
    parser.add_argument(
        "--filter-tag",
        type=str,
        metavar="TAG",
        help="Filter total strike count by this tag (implies --count).",
    )
    parser.add_argument(
        "count_to_add",
        type=int,
        nargs="?",
        default=None,
        help="Number of strikes to add (required if not querying).",
    )
    parser.add_argument(
        "session_tag",
        type=str,
        nargs="?",
        default=None,
        help="Optional tag for the session (used only when adding strikes).",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    args = parser.parse_args(argv)

    if args.info:
        args.operation_mode = "info"
    elif args.detail:
        args.operation_mode = "detail"
    elif args.summary:
        args.operation_mode = "summary"
    elif args.count or args.filter_tag:
        args.operation_mode = "count_total"
    elif args.count_to_add is not None:
        args.operation_mode = "add_entry"
    else:
        parser.error(
            "<count_to_add> is required unless using --info, --count, --filter-tag, --summary, or --detail."
        )

    if args.operation_mode == "info":
        conflicting_args_for_info = [
            args.count_to_add,
            args.session_tag,
            args.count,
            args.summary,
            args.detail,
            args.filter_tag,
            args.by_date,
        ]
        if any(
            arg is not None and arg is not False for arg in conflicting_args_for_info
        ):
            parser.error(
                "--info cannot be used with other operational arguments like <count_to_add>, [session_tag], --count, --summary, --detail, --filter-tag, or --by-date."
            )
    if args.operation_mode == "add_entry":
        if args.session_tag is not None and args.count_to_add is None:
            parser.error(
                "[session_tag] can only be used when <count_to_add> is also provided."
            )
        conflicting_flags_for_add = [
            args.count,
            args.summary,
            args.detail,
            args.filter_tag,
            args.by_date,
            args.info,
        ]
        if any(flag for flag in conflicting_flags_for_add):
            parser.error(
                "Operational flags like --count, --summary, --detail, --filter-tag, --by-date, --info cannot be used when <count_to_add> is provided."
            )
    if args.operation_mode == "count_total":
        if args.count_to_add is not None or args.session_tag is not None:
            parser.error(
                "<count_to_add> and [session_tag] cannot be used with --count or --filter-tag."
            )
        if args.summary or args.detail or args.info or args.by_date:
            parser.error(
                "--summary, --detail, --info, or --by-date cannot be used with --count or --filter-tag."
            )

    if args.operation_mode == "summary":
        if args.count_to_add is not None or args.session_tag is not None:
            parser.error(
                "<count_to_add> and [session_tag] cannot be used with --summary."
            )
        if args.count or args.filter_tag or args.detail or args.info or args.by_date:
            parser.error(
                "--count, --filter-tag, --detail, --info, or --by-date cannot be used with --summary."
            )

    if args.operation_mode == "detail":
        if args.count_to_add is not None or args.session_tag is not None:
            parser.error(
                "<count_to_add> and [session_tag] cannot be used with --detail."
            )
        if args.count and not args.filter_tag:
            parser.error(
                "Explicit --count cannot be used with --detail. Use --filter-tag for filtering details."
            )
        if args.summary or args.info:
            parser.error("--summary or --info cannot be used with --detail.")
    return args


def main(argv: list[str] | None = None) -> int:
    """
    Main function to run the shock wave counter application.

    Parses arguments, sets up logging, initializes the App,
    and executes the requested operation.

    :param argv: Optional list of command-line arguments.
    :type argv: list[str] | None
    :return: Exit code (0 for success, 1 for error).
    :rtype: int
    """
    args = _parse_arguments(argv)

    logger_name = constants.APP_NAME
    logger = Logger(name=logger_name, debug=args.debug)
    logger.debug(f"Application started with arguments: {args}")

    try:
        app = App(db_path=constants.DEFAULT_DB_FILE, logger=logger)

        if args.operation_mode == "info":
            logger.debug("Operating in info display mode.")
            app.display_app_info()
        elif args.operation_mode == "detail":
            logger.debug("Operating in detail query mode.")
            app.query_strike_details(
                filter_tag=args.filter_tag, group_by_date=args.by_date
            )
        elif args.operation_mode == "summary":
            logger.debug("Operating in summary mode.")
            app.query_summary()
        elif args.operation_mode == "count_total":
            logger.debug("Operating in query total strikes mode.")
            app.query_total_strikes(filter_tag=args.filter_tag)
        elif args.operation_mode == "add_entry":
            logger.debug("Operating in add entry mode.")
            app.add_strike_entry(
                count_to_add=args.count_to_add, session_tag=args.session_tag
            )

    except ValueError as ve:
        logger.error(f"Input validation error: {ve}")
        print(f"Error: {ve}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}", exc_info=args.debug)
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return 1

    logger.debug("Application finished successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
