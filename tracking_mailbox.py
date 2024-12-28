import mailbox
import os
from tqdm import tqdm


class TrackingMbox(mailbox.mbox):
    def __init__(self, path, factory=None, create=True, progress_callback=None, print_progress=False, max_messages=None):
        """
        Initialize a TrackingMbox object, which extends the standard mailbox.mbox with progress tracking capabilities.

        Parameters:
        path (str): The file path to the mbox file.
        factory (callable, optional): A callable object that creates message objects. If None, 
                                      rfc822.Message is used. Defaults to None.
        create (bool, optional): If True, the file will be created if it doesn't exist. Defaults to True.
        progress_callback (callable, optional): A function to be called with the current progress percentage. 
                                                The function should accept a single float argument. Defaults to None.
        print_progress (bool, optional): If True, a progress bar will be displayed using tqdm. Defaults to False.
        max_messages (int, optional): The maximum number of messages to process. If None, all messages 
                                      will be processed. Defaults to None.
        """

        super().__init__(path, factory, create)
        self.progress_callback = progress_callback
        self._total_size = os.path.getsize(path)
        self._processed_size = 0
        self.print_progress = print_progress
        self.pbar = None
        self.max_messages = max_messages


    
    def _generate_toc(self):
        """Override the internal TOC generation to add progress tracking"""
        starts, stops = [], []
        last_was_empty = False
        self._file.seek(0)

        if self.print_progress:
            self.pbar = tqdm(total=100, unit='%', desc='Reading mbox')

        
        while True:
            line_pos = self._file.tell()
            line = self._file.readline()
            self._processed_size = line_pos
            
            if line.startswith(b'From '):
                if len(stops) < len(starts):
                    if last_was_empty:
                        stops.append(line_pos - len(os.linesep))
                    else:
                        stops.append(line_pos)
                starts.append(line_pos)
                last_was_empty = False

                # Check if we've reached the max_messages limit
                if self.max_messages is not None and len(starts) >= self.max_messages:
                    stops.append(self._file.tell())
                    break

            elif not line:
                if last_was_empty:
                    stops.append(line_pos - len(os.linesep))
                else:
                    stops.append(line_pos)
                break
            elif line == os.linesep:
                last_was_empty = True
            else:
                last_was_empty = False
            
            if self.progress_callback:
                progress = (self._processed_size / self._total_size) * 100
                self.progress_callback(progress)
            
            if self.print_progress:
                new_progress = int((self._processed_size / self._total_size) * 100)
                self.pbar.update(new_progress - self.pbar.n)

        self._toc = dict(enumerate(zip(starts, stops)))
        self._next_key = len(self._toc)
        self._file_length = self._file.tell()

        # Call progress_callback one last time to ensure 100% is reported
        if self.progress_callback:
            self.progress_callback(100)

        if self.print_progress:
            self.pbar.close()

