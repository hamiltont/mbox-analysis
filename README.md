# Mbox Sender Frequency

This very small tool will display mail counts grouped by sender. This is helpful to identify automated notification mails that you may want to delete from your mailbox to free up some space.

If you're curious, I wrote a [blogpost](https://blog.dipasquale.fr) in which I explain the context in which I needed this script, namely to leave GMail.

## Usage

Clone this repo somewhere or download the standalone python script. You can then simply use it with :

```
python list_senders.py [-h] [--threshold THRESHOLD] [--group-by-email]
                       mbox_path
```

for example :

![usage example](https://i.imgur.com/isCPq3N.png)

## Getting your mbox file from GMail

Head to [Google Takeout](https://takeout.google.com), select Mails, and opt for the file download link version. Then be patient, and you will receive a mail with a link to your own mbox file within a few hours / days.

## Limitations

This was not optimized at all, so it may be quite slow, however it ran on my 4GB file within a few minutes, which was acceptable to me.


## Useful Arguments

Here's a list of potentially confusing arguments with more detailed explanations:

### --from / -f (strip_emails)

This argument controls how the 'From' field of emails is processed for grouping.

- If not used (default behavior, strip_emails=True): The script will extract only the email address from the 'From' field. This means "John Doe <john@example.com>" and "Jane Doe <john@example.com>" would be grouped together under "john@example.com".

- If used (strip_emails=False): The script will use the entire 'From' field for grouping. This means "John Doe <john@example.com>" and "Jane Doe <john@example.com>" would be treated as separate entries.

Use this flag when you want to distinguish between different senders who might be using the same email address but with different display names.

### --count / -c (report_size)

This argument determines whether the script counts emails or counts email size in bytes.

- If not used (default behavior, report_size=True): The script will calculate and report the total size of emails from each sender.

- If used (report_size=False): The script will count and report the number of emails from each sender.

Use this flag when you're more interested in the frequency of emails rather than the amount of data sent by each sender.



## Setup and Installation

To run this script, you'll need Python 3.0 or higher. Here's how to set up your environment:

1. Create a virtual environment:

```sh
python3 -m venv venv
```

2. Activate the virtual environment:
  ```sh
  source venv/bin/activate
  ```

3. Install the required packages:

pip install -r requirements.txt

4. Run the script:

python list_senders.py /path/to/your/mbox_file


Remember to replace `/path/to/your/mbox_file` with the actual path to your mbox file.

