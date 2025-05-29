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
            message = f"Successfully added {count_to_add} strikes." + (f" with tag '{processed_tag}'" if processed_tag else "")
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
            sorted_tags = sorted(
                tag_summaries.keys(), key=lambda t: (t is None, t)
            )

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


def _parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
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
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug logging."
    )
    args = parser.parse_args(argv)

    # Validate argument combinations
    is_add_mode = args.count_to_add is not None
    is_count_mode = args.count
    is_filter_tag_mode = args.filter_tag is not None
    is_summary_mode = args.summary

    # Count how many primary modes are selected
    modes_selected = sum([is_add_mode and not (is_count_mode or is_filter_tag_mode or is_summary_mode),
                          is_count_mode and not is_filter_tag_mode, # --count alone
                          is_filter_tag_mode, # --filter-tag implies count
                          is_summary_mode])


    if is_summary_mode:
        if args.count or args.filter_tag or args.count_to_add or args.session_tag:
            parser.error(
                "--summary cannot be used with --count, --filter-tag, <count_to_add>, or [session_tag]."
            )
    elif is_count_mode or is_filter_tag_mode:
        if args.count_to_add is not None or args.session_tag is not None:
            parser.error(
                "Positional arguments <count_to_add> and [session_tag] "
                "are not allowed with --count or --filter-tag."
            )
        if is_filter_tag_mode: # Implicitly enable count mode if filter_tag is used
            args.count = True
    elif args.count_to_add is None: # This means we are in add mode by default but no count_to_add
         parser.error(
            "<count_to_add> is required unless using --count, --filter-tag, or --summary."
        )

    # Ensure only one primary operation mode is effectively chosen
    # (add, count, filter-tag (which is a form of count), summary)
    # Add mode is when count_to_add is present AND no query/summary flags are set.

    active_modes = []
    if args.summary:
        active_modes.append("--summary")
    if args.count or args.filter_tag: # filter_tag implies count
        active_modes.append("--count/--filter-tag")
    if args.count_to_add is not None and not (args.summary or args.count or args.filter_tag):
        active_modes.append("add_entry")

    if len(active_modes) > 1:
        parser.error(f"Too many operations specified. Choose one of: add entry, --count, --filter-tag, --summary. Got: {', '.join(active_modes)}")
    elif not active_modes and args.count_to_add is None: # No operation and no count_to_add for default add mode
        parser.error(
            "No operation specified. Provide <count_to_add> or use --count, --filter-tag, or --summary."
        )


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

        if args.summary:
            logger.debug("Operating in summary mode.")
            app.query_summary()
        elif args.count or args.filter_tag is not None:
            logger.debug("Operating in query total strikes mode.")
            app.query_total_strikes(filter_tag=args.filter_tag)
        elif args.count_to_add is not None:
            logger.debug("Operating in add entry mode.")
            app.add_strike_entry(
                count_to_add=args.count_to_add, session_tag=args.session_tag
            )
        else:
            # This case should be caught by _parse_arguments.
            # If it's reached, it indicates a logic flaw in argument parsing.
            logger.error(
                "Reached unexpected state in main dispatch. Argument parsing may be flawed."
            )
            # Re-running _parse_arguments with --help to show usage.
            # This is a fallback, ideally _parse_arguments should prevent this.
            _parse_arguments(["--help"])
            return 1

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
