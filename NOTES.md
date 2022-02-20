Use unpacking for stream from serial:

```
def word_to_decimal(byte1, byte2):
    return byte1 + (byte2 * 256)

serial_raw = 'OK 3 00 11 22 33 44 55 66 77 88 99'
serial_line = serial_raw.split(' ')
serial = {
    "node": int(serial_line[1],
    "lowbat": word_to_decimal(serial_line[2], serial_line[3]),
    "port1": word_to_decimal(serial_line[4], serial_line[5]),
    "port2": word_to_decimal(serial_line[6], serial_line[7]),
    "port3": word_to_decimal(serial_line[8], serial_line[9]),
    "port4": word_to_decimal(serial_line[10], serial_line[11]),
    }
print(serial['node'])
print(serial['port1'])
```

Could also build up a tuple but would likely be hard to read

Another option although slower to get byte values, only works in python3

```
print( int.from_bytes([240, 4], byteorder='little') )
# that's a lot slower than doing either of these, which take about the same time and are much faster
print( 240 + (4 * 256) )
print( 240 + (4 << 8) )
# but int.from_bytes() is easier to read and in this case where it's called a handful of times it's not a big deal
```

Currently it's not handling negative numbers correctly.  For example the bytes `143 98` should translate to `-369` but ends up printing `25231`. Subtracting that number by `25600` gives correct value. Some examples

```
>>> int.from_bytes([143, 98], byteorder='little', signed=True)
25231
>>> int.from_bytes([143, 98], byteorder='little', signed=True) - 25600
-369
>>> 2**15
32768
>>> list(int.to_bytes(2**15 - 1, 2, 'little', signed=True))
[255, 127]
>>> bin(2**15 - 1)
'0b111111111111111'
>>> -1 * 2**15 + 1
-32767
>>> list(int.to_bytes(-1 * 2**15 + 1, 2, 'little', signed=True))
[1, 128]
>>> bin(-1 * 2**15 + 1)
'-0b111111111111111'
```

So I guess check the second byte is over 127 and if it is subtact 25600.  Unsure why it has to do that because it still returns `-369` so need to divide by `100` to get the float value.

some more playing around with structs although now I realized the issue before was with the board itself reading the temperature unsigned and not making it a signed number.  Fixing that fixed the output.

```
>>> import struct
>>> s = struct.Struct('< b h h h h h')
>>> values = (2, 0, 837, 0, 0, 0)
>>> s.pack(*values)
b'\x02\x00\x00E\x03\x00\x00\x00\x00\x00\x00'
>>> list(s.pack(*values))
[2, 0, 0, 69, 3, 0, 0, 0, 0, 0, 0]
>>> values = (2, 0, 0, 69, 3, 0, 0, 0, 0, 0, 0)
>>> values = bytearray([2, 0, 0, 69, 3, 0, 0, 0, 0, 0, 0])
>>> s.unpack(values)
(2, 0, 837, 0, 0, 0)
>>> values = bytearray([2, 0, 0, 143, 98, 0, 0, 0, 0, 0, 0])
>>> s.unpack(values)
(2, 0, 25231, 0, 0, 0)
>>> values = (2, 0, -369, 0, 0, 0)
>>> list(s.pack(*values))
[2, 0, 0, 143, 254, 0, 0, 0, 0, 0, 0]
```


## Using dataflash stuff

Resonse at startup:

```
DF I 1855 147
```

- `1855` - last page
- `147` - sequence number

Periodically:

```
DF S 1856 147 1
```

- `1856` - last page saved
- `147` - sequence number
- `1` - timestamp (at the very least resets when device is reconnected)

To play back data send:

```
0,147,0,0,7,67r
```

- `0,147` is the sequence number (two byte short (number))
- `0,0,7,67` is the time stamp to start from (four byte integer) this comes to 1859

To create these in python:

```
>>> import struct
>>> start_ts = struct.pack('>I', 1859)
>>> start_ts
b'\x00\x00\x07C'
>>> list(start_ts)
[0, 0, 7, 67]
>>> struct.pack('>H', 147)
b'\x00\x93'
>>> sequence_number = struct.pack('>H', 147)
>>> sequence_number
b'\x00\x93'
>>> list(sequence_number)
[0, 147]
```

In python 3

```
>>> start_ts = (1859).to_bytes(4, byteorder='big')
>>> start_ts
b'\x00\x00\x07C'
>>> list(start_ts)
[0, 0, 7, 67]
>>> sequence_number = (147).to_bytes(2, byteorder='big')
>>> sequence_number
b'\x00\x93'
>>> list(sequence_number)
[0, 147]
```

Can just specify the sequence number to play back all data in that sequence, it will then increment the sequence counter.  Likely won't use any of this since it would involve figuring out how far back a value was reported which should be possible

## creating dictionary from keys

Not sure if this will help much but I just found it

```
>>> print(dict.fromkeys(['node','lowbatt','port1','port2','port3','port4']))
{'node': None, 'lowbatt': None, 'port1': None, 'port2': None, 'port3': None, 'port4': None}
```

## Use slots to optimize code, if needed

See <https://tech.oyster.com/save-ram-with-python-slots/>

## Schema

- db name: jeelink
- example (in influxdb line protocol format)

    sensor,location=garage low_batt=false,temp=20.34,door_open=false
    sensor,location=basement low_batt=false,temp=20.43,humidity=34.5,water_detected=false

## still not working when below zero:

```
2020-02-08 02:30:45.275 | DEBUG    | __main__:main:80 - b'OK 2 0 0 106 1 0 0 0 0 0 0'
2020-02-08 02:30:45.275 | INFO     | __main__:main:94 - {'node': 2, 'lowbatt': 0, 'port1': 362, 'port2': 0, 'port3': 0, 'port4': 0}
```

