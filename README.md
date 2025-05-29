# Shock Wave Counter (swc)

A simple command-line tool to track the total strikes made by an extracorporeal shock wave machine.

## Purpose

This application provides a quick and easy way for users to:
*   Record the number of shock wave strikes administered during a session.
*   Optionally tag each session for later filtering.
*   Query the total number of strikes, either overall or filtered by a specific tag.

Data is stored locally in an SQLite database.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/thehunmonkgroup/shock_wave_counter.git
    cd shock_wave_counter
    ```
2.  Install the package (preferably in a virtual environment):
    ```bash
    pip install .
    ```
    This will make the `swc` command available in your environment.

## Usage

The `swc` command is used to interact with the strike counter.

### Adding Strike Entries

To add a new strike entry, provide the number of strikes as the first argument. You can optionally provide a session tag as a second argument.

*   **Add strikes without a tag:**
    ```bash
    swc <count_to_add>
    ```
    Example:
    ```bash
    swc 1500
    ```
    Output:
    ```
    Successfully added 1500 strikes.
    ```

*   **Add strikes with a tag:**
    The tag will be converted to lowercase for consistency.
    ```bash
    swc <count_to_add> <session_tag>
    ```
    Example:
    ```bash
    swc 2000 ShoulderSession
    ```
    Output:
    ```
    Successfully added 2000 strikes. with tag 'shouldersession'
    ```

### Querying Total Strikes

To query the total number of strikes, use the `-c` or `--count` option. You can also filter the count by a specific tag using `--filter-tag`.

*   **Get total strikes (all entries):**
    ```bash
    swc --count
    ```
    Example Output:
    ```
    Total strikes: 3500
    ```
    Or, if no strikes have been recorded:
    ```
    No strikes recorded yet.
    ```

*   **Get total strikes for a specific tag:**
    The tag for filtering is case-insensitive.
    ```bash
    swc --filter-tag <tag_value>
    ```
    (Note: `--count` is implied if `--filter-tag` is used, but can also be explicitly stated: `swc --count --filter-tag <tag_value>`)
    Example:
    ```bash
    swc --filter-tag shouldersession
    ```
    Example Output:
    ```
    Total strikes for tag 'shouldersession': 2000
    ```
    Or, if no strikes are found for that tag:
    ```
    No strikes found for tag 'shouldersession'.
    ```

### Displaying a Summary

To display a summary of all strikes, grouped by tag, along with a grand total, use the `--summary` option.

*   **Get strike summary:**
    ```bash
    swc --summary
    ```
    Example Output (if entries exist):
    ```
    Strike Summary:
      Tag 'backsess': 1000 strikes
      Tag 'shouldersession': 2000 strikes
      Untagged: 1500 strikes
    --------------------
    Grand Total: 4500 strikes
    ```
    If no strikes have been recorded:
    ```
    No strikes recorded yet.
    ```
    The `--summary` option cannot be used with `<count_to_add>`, `[session_tag]`, `--count`, or `--filter-tag`.

### Debug Mode

For more verbose output, including detailed logging of operations, use the `--debug` flag with any command:

```bash
swc --debug 100 mytag
swc --debug --count --filter-tag mytag
```

### Database Location

By default, the SQLite database (`strikes.db`) is stored in:
`~/.local/share/shock_wave_counter/strikes.db`

The application will create this directory and file if they do not exist.
