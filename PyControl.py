from array import array
import pyb

class Ring_buffer():
    # Generic ring buffer class using array object to hold items.  All item in the 
    # ring buffer must be of the same type, specified at initialisation by typecode argument.

    def __init__(self, typecode = 'i', buffer_length = 10, null_value = -1):
        self.typecode = typecode
        self.null_value = null_value
        self.buffer_length = buffer_length
        self.reset()

    def reset(self):
        self.buffer = array(self.typecode, [self.null_value] * self.buffer_length)
        self.read_index  = 0
        self.write_index = 0

    def put(self, value):
        assert self.buffer[self.write_index] == self.null_value, 'Buffer full'
        self.buffer[self.write_index] = value
        self.write_index = (self.write_index + 1) % self.buffer_length

    def get(self):
        value = self.buffer[self.read_index]
        self.buffer[self.read_index] = self.null_value
        if value != self.null_value:
            self.read_index = (self.read_index + 1) % self.buffer_length
        return value

class Event_buffer():
    # Generic ring buffer class using array object to hold items.  All item in the 
    # ring buffer must be of the same type, specified at initialisation by typecode argument.

    def __init__(self, buffer_length = 10):
        self.ID_null_value = -1  # ID null value.
        self.TS_null_value =  0  # Time stamp null value.       
        self.buffer_length = buffer_length
        self.reset()

    def reset(self):
        self.ID_buffer = array('i', [self.ID_null_value] * self.buffer_length)
        self.TS_buffer = array('L', [self.TS_null_value] * self.buffer_length)
        self.read_index  = 0
        self.write_index = 0

    def put(self, ID, timestamp = None):
        assert self.ID_buffer[self.write_index] == self.ID_null_value, 'Buffer full'
        if not timestamp:
            timestamp = pyb.millis()
        self.ID_buffer[self.write_index] = ID
        self.TS_buffer[self.write_index] = timestamp
        self.write_index = (self.write_index + 1) % self.buffer_length

    def get(self):
        ID = self.ID_buffer[self.read_index]
        timestamp =  self.TS_buffer[self.read_index] 
        self.ID_buffer[self.read_index] = self.ID_null_value
        self.TS_buffer[self.read_index] = self.TS_null_value
        if ID != self.ID_null_value:
            self.read_index = (self.read_index + 1) % self.buffer_length
        return (ID, timestamp)

# class Int_events():
#     # Class for attaching external interupts to event buffers.
#     def __init__(self):
