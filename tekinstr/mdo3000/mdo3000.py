"""MDO3000 Series Oscilloscope"""
import re
from tekinstr.model import Model
from tekinstr.mdo3000.oscilloscope import Oscilloscope
from tekinstr.common import validate


class MDO3000(Model):
    """MDO3000 Series Oscilloscope class

    Attributes:
        resource (pyvisa.resources.Resource): pyvisa resource
    """

    def __init__(self, visa):
        super().__init__(visa)
        n_channels = 4
        self.oscilloscope = Oscilloscope(self, n_channels)
        self._display = self._get_select()[0]


    def _get_select(self):
        """Get the current display selection"""
        original_header_state = self._visa.query("HEADER?")
        self._visa.write("HEADER ON")
        select_str = self._visa.query("SELECT?").replace(":SELECT:", "")
        raw_select = dict([kv.split(" ", maxsplit=1) for kv in select_str.split(";")])
        displayed_channels = set()
        control_channel = raw_select.pop("CONTROL", None)
        for k, v in raw_select.items():
            if v in ["1", "ON"]:
                k = "RF" if k.startswith("RF") else k
                displayed_channels.add(k)
        self._visa.write(f"HEADER {original_header_state}")
        return (displayed_channels, control_channel)

    @property
    def display(self):
        """channel(s) (str, list): display the given channel(s);
        'CHx', 'CHx:y', ['CHx', 'CHy'], or 'RF'
        The oscilloscope and spectrum analyzer are mutually exclusive systems and
        cannot be displayed simultaneously.
        """
        self._display = self._get_select()[0]
        return self._display

    @display.setter
    @validate
    def display(self, channels):
        chs = []
        if isinstance(channels, str) and channels.startswith("CH"):
            match = re.match("^CH(?P<first>[1-4])(?P<last>:[1-4])?$", channels)
            if match is None:
                raise ValueError(f"{channels} not a valid specification")
            first = int(match.group("first"))
            last = match.group("last")
            if last is None:
                last = first
            else:
                last = int(last[-1])
            for ch in range(first, last + 1):
                chs.append(f"CH{ch}")
            channels = chs
        elif isinstance(channels, str) and channels.startswith("RF"):
            channels = ["RF_NORMAL"]
        channels = set(channels)
        displayed_channels = self.display
        for channel in displayed_channels - channels:
            self._visa.write(f"SELECT:{channel} OFF")
        for channel in channels - displayed_channels:
            self._visa.write(f"SELECT:{channel} ON")
        self._display = self._get_select()[0]

    def save_image(self, path, fileformat="png"):
        """Save screen image to 'path'

        Parameters
        ----------
        path : str
            path including file name e.g. 'E:/myimage.png'
            If path is only a file name, image will be saved to the instrument's
            file system current working directory.
        fileformat : str
            fileformat of image {'png', 'bmp', 'tiff'}
        """
        self._visa.write(f"SAVE:IMAGE:FILEFORMAT {fileformat}")
        self._visa.write(f"SAVE:IMAGE '{path}'")

    def show_message(self, message):
        """Show message on display

        Parameters
        ----------
        message : str
            text to display
        """
        self._visa.write(f"MESSAGE:SHOW '{message}'")
        self._visa.write("MESSAGE:STATE ON")

    def clear_message(self):
        """Remove message from display"""
        self._visa.write("MESSAGE:CLEAR")
        self._visa.write("MESSAGE:STATE OFF")
