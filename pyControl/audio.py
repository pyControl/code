import pyb
import math
import builtins
import struct
import sys
import gc
from ucollections import namedtuple

_sine_len = 100 # Number of points in sine wave.
_sine_buf = bytearray([128+int(127*math.sin(2*math.pi*i/_sine_len)) for i in range(_sine_len)])
_sqr_buf = bytearray([255,0])
_click_buf = bytearray([255,0,255,255,0,0]+4*[255]+4*[0]+8*[255]+8*[0]
                       +16*[255]+16*[0]+32*[255]+32*[0]+[128])
_off_buf = bytearray([128])

#-----------------------------------------------------------------------------------
# Audio output
#-----------------------------------------------------------------------------------

class Audio_output():
    def __init__(self, channel=1):
        assert channel in [1,2], '! Channel number invalid, must be 1 or 2.'
        self._DAC = pyb.DAC(channel) 
        self._timer = pyb.Timer(channel)
        self._playing = False
        self._func = None # Function currently being used for sweeped sound (sine, square or noise)
        self._freq = 0
        self._freq_ind = 0

    # User functions-------------------------------------------------------------------

    def off(self):
            self._DAC.write_timed(_off_buf, 10000, mode=pyb.DAC.NORMAL)
            self._timer.deinit()
            self._playing = False

    def sine(self, freq):  # Play a sine wave tone at the specified frequency.
        self._DAC.write_timed(_sine_buf, freq*_sine_len, mode=pyb.DAC.CIRCULAR)

    def square(self, freq): # Play a square wave tone at the specified frequency.
        self._DAC.write_timed(_sqr_buf, freq*2, mode=pyb.DAC.CIRCULAR)    

    def noise(self, freq=10000): # Play white noise with specified maximum frequency.
        self._DAC.noise(freq*2)

    def clicks(self, rate): # Play clicks at specified rate.
        self._timer.init(freq=rate)
        self._timer.callback(self._click)

    def pulsed_sine(self, freq, pulse_rate): # Play a sine wave pulsed at the specified rate.
        self._pulsed_sound(freq, pulse_rate, self.sine)

    def pulsed_square(self, freq, pulse_rate): # Play a square wave pulsed at the specified rate.
        self._pulsed_sound(freq, pulse_rate, self.square)

    def pulsed_noise(self, freq, pulse_rate):
        self._pulsed_sound(freq, pulse_rate, self.noise)

    def stepped_sine(self, start_freq, end_freq, n_steps, step_rate):
        self._sound_step(start_freq, end_freq, n_steps, step_rate, self.sine)

    def stepped_square(self, start_freq, end_freq, n_steps, step_rate):
        self._sound_step(start_freq, end_freq, n_steps, step_rate, self.square)

    def play_wav(self, file_name, gc_collect=True):
        f = Wave_read(file_name)
        self._DAC.write_timed(f.readframes(f._nframes), f._framerate)
        f.close()
        if gc_collect: gc.collect()

    # Support functions-----------------------------------------------------------------

    def _click(self, timer=None): # Play a single click.
        self._DAC.write_timed(_click_buf, 40000, mode=pyb.DAC.NORMAL)  

    def _pulsed_sound(self, freq, pulse_rate, func):
        self._freq = freq
        self._func = func
        self._timer.init(freq=2*pulse_rate)
        self._timer.callback(self._toggle_sound)

    def _toggle_sound(self, timer):
        if self._playing:
            self._DAC.write(127)
            self._playing = False
        else:
            self._func(self._freq)
            self._playing = True

    def _sound_step(self, start_freq, end_freq, n_steps, step_rate, func):
        freq_ratio = (end_freq/start_freq)**(1./(n_steps-1))
        self._freq = [int(start_freq * (freq_ratio**i)) for i in range(n_steps)]
        self._freq_ind = 0
        self._func = func
        self._timer.init(freq=step_rate)
        self._timer.callback(self._step_sound)

    def _step_sound(self, timer): # Timer callback to increment frequency during sweeped sounds.
        self._func(self._freq[self._freq_ind])
        self._freq_ind = (self._freq_ind+1) % len(self._freq)
        
#---------------------------------------------------------------------------------------------------
# Wave: Read audio from wav files, see http://micropython.org/resources/examples/wave.py
#---------------------------------------------------------------------------------------------------

__all__ = ["open", "Error"]

class Error(Exception):
    pass

WAVE_FORMAT_PCM = 0x0001

_array_fmts = None, 'b', 'h', None, 'i'

_wave_params = namedtuple('_wave_params',
                     'nchannels sampwidth framerate nframes comptype compname')

class Wave_read:
    '''Class for reading data from a .wav file'''

    def initfp(self, file):
        self._convert = None
        self._soundpos = 0
        self._file = Chunk(file, bigendian = 0)
        if self._file.getname() != b'RIFF':
            raise Error('file does not start with RIFF id')
        if self._file.read(4) != b'WAVE':
            raise Error('not a WAVE file')
        self._fmt_chunk_read = 0
        self._data_chunk = None
        while 1:
            self._data_seek_needed = 1
            try:
                chunk = Chunk(self._file, bigendian = 0)
            except EOFError:
                break
            chunkname = chunk.getname()
            if chunkname == b'fmt ':
                self._read_fmt_chunk(chunk)
                self._fmt_chunk_read = 1
            elif chunkname == b'data':
                if not self._fmt_chunk_read:
                    raise Error('data chunk before fmt chunk')
                self._data_chunk = chunk
                self._nframes = chunk.chunksize // self._framesize
                self._data_seek_needed = 0
                break
            chunk.skip()
        if not self._fmt_chunk_read or not self._data_chunk:
            raise Error('fmt chunk and/or data chunk missing')

    def __init__(self, f):
        self._i_opened_the_file = None
        if isinstance(f, str):
            f = builtins.open(f, 'rb')
            self._i_opened_the_file = f
        # else, assume it is an open file object already
        try:
            self.initfp(f)
        except:
            if self._i_opened_the_file:
                f.close()
            raise

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    #
    # User visible methods.
    #
    def getfp(self):
        return self._file

    def rewind(self):
        self._data_seek_needed = 1
        self._soundpos = 0

    def close(self):
        if self._i_opened_the_file:
            self._i_opened_the_file.close()
            self._i_opened_the_file = None
        self._file = None

    def setpos(self, pos):
        if pos < 0 or pos > self._nframes:
            raise Error('position not in range')
        self._soundpos = pos
        self._data_seek_needed = 1

    def readframes(self, nframes):
        if self._data_seek_needed:
            self._data_chunk.seek(0, 0)
            pos = self._soundpos * self._framesize
            if pos:
                self._data_chunk.seek(pos, 0)
            self._data_seek_needed = 0
        if nframes == 0:
            return b''
        data = self._data_chunk.read(nframes * self._framesize)
        if self._sampwidth != 1 and sys.byteorder == 'big':
            data = audioop.byteswap(data, self._sampwidth)
        if self._convert and data:
            data = self._convert(data)
        self._soundpos = self._soundpos + len(data) // (self._nchannels * self._sampwidth)
        return data

    #
    # Internal methods.
    #

    def _read_fmt_chunk(self, chunk):
        wFormatTag, self._nchannels, self._framerate, dwAvgBytesPerSec, wBlockAlign = struct.unpack('<HHLLH', chunk.read(14))
        if wFormatTag == WAVE_FORMAT_PCM:
            sampwidth = struct.unpack('<H', chunk.read(2))[0]
            self._sampwidth = (sampwidth + 7) // 8
        else:
            raise Error('unknown format: %r' % (wFormatTag,))
        self._framesize = self._nchannels * self._sampwidth
        self._comptype = 'NONE'
        self._compname = 'not compressed'

#---------------------------------------------------------------------------------------------------
# Chunk: Class to read IFF chunks, see http://micropython.org/resources/examples/chunk.py
#---------------------------------------------------------------------------------------------------

class Chunk:
    
    def __init__(self, file, align=True, bigendian=True, inclheader=False):
        import struct
        self.closed = False
        self.align = align      # whether to align to word (2-byte) boundaries
        if bigendian:
            strflag = '>'
        else:
            strflag = '<'
        self.file = file
        self.chunkname = file.read(4)
        if len(self.chunkname) < 4:
            raise EOFError
        try:
            data = file.read(4)
            self.chunksize = struct.unpack(strflag+'L', data)[0]
        except:# struct.error:
            raise EOFError
        if inclheader:
            self.chunksize = self.chunksize - 8 # subtract header
        self.size_read = 0
        try:
            self.offset = self.file.tell()
        except:
            self.seekable = False
        else:
            self.seekable = True

    def getname(self):
        """Return the name (ID) of the current chunk."""
        return self.chunkname

    def getsize(self):
        """Return the size of the current chunk."""
        return self.chunksize

    def close(self):
        if not self.closed:
            self.skip()
            self.closed = True

    def isatty(self):
        if self.closed:
            raise ValueError("I/O operation on closed file")
        return False

    def seek(self, pos, whence=0):
        """Seek to specified position into the chunk. Default position is 0 (start of chunk)."""

        if self.closed:
            raise ValueError("I/O operation on closed file")
        if not self.seekable:
            raise OSError("cannot seek")
        if whence == 1:
            pos = pos + self.size_read
        elif whence == 2:
            pos = pos + self.chunksize
        if pos < 0 or pos > self.chunksize:
            raise RuntimeError
        self.file.seek(self.offset + pos, 0)
        self.size_read = pos

    def tell(self):
        if self.closed:
            raise ValueError("I/O operation on closed file")
        return self.size_read

    def read(self, size=-1):
        """Read at most size bytes from the chunk."""

        if self.closed:
            raise ValueError("I/O operation on closed file")
        if self.size_read >= self.chunksize:
            return ''
        if size < 0:
            size = self.chunksize - self.size_read
        if size > self.chunksize - self.size_read:
            size = self.chunksize - self.size_read
        data = self.file.read(size)
        self.size_read = self.size_read + len(data)
        if self.size_read == self.chunksize and \
           self.align and \
           (self.chunksize & 1):
            dummy = self.file.read(1)
            self.size_read = self.size_read + len(dummy)
        return data

    def skip(self):
        """Skip the rest of the chunk."""

        if self.closed:
            raise ValueError("I/O operation on closed file")
        if self.seekable:
            try:
                n = self.chunksize - self.size_read
                # maybe fix alignment
                if self.align and (self.chunksize & 1):
                    n = n + 1
                self.file.seek(n, 1)
                self.size_read = self.size_read + n
                return
            except OSError:
                pass
        while self.size_read < self.chunksize:
            n = min(8192, self.chunksize - self.size_read)
            dummy = self.read(n)
            if not dummy:
                raise EOFError