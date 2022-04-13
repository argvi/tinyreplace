#!/usr/bin/env python3

import codecs
import struct
from datetime import datetime, timedelta
from PIL import Image

R_PLACE_DATA_TIME_FMT = '%Y-%m-%d %H:%M:%S.%f %Z'
R_PLACE_DATA_TIME_FMT_NO_MILS = '%Y-%m-%d %H:%M:%S %Z'
R_PLACE_START_DT = datetime.strptime('2022-04-01 12:44:10.315 UTC',
                                     R_PLACE_DATA_TIME_FMT)
R_PLACE_COLORS = ['#FF3881',
                  '#7EED56',
                  '#51E9F4',
                  '#BE0039',
                  '#00A368',
                  '#00CC78',
                  '#FF99AA',
                  '#493AC1',
                  '#2450A4',
                  '#009EAA',
                  '#00756F',
                  '#811E9F',
                  '#000000',
                  '#D4D7D9',
                  '#FFD635',
                  '#FFFFFF',
                  '#FFA800',
                  '#3690EA',
                  '#898D90',
                  '#6A5CFF',
                  '#6D482F',
                  '#9C6926',
                  '#FF4500',
                  '#B44AC0',
                  '#E4ABFF',
                  '#94B3FF',
                  '#00CCC0',
                  '#515252',
                  '#6D001A',
                  '#DE107F',
                  '#FFB470',
                  '#FFF8B8']

# miliseconds from start,uid,color,x,y
R_PLACE_UID_PIXEL = struct.Struct('I64sBHH')
R_PLACE_ANON_PIXEL = struct.Struct('IBHH')  # miliseconds from start,color,x,y

ANON_UID = 'A' * 88


class Writer(object):
    def __init__(self, fileobj, with_uids=False):
        self.fileobj = fileobj
        self.with_uids = with_uids

        if self.with_uids:
            self.fileobj.write(b'\x01')
        else:
            self.fileobj.write(b'\x00')

    def writerow(self, row):
        ts, uid, color, coords = row
        try:
            ts = datetime.strptime(ts, R_PLACE_DATA_TIME_FMT)
        except ValueError:
            ts = datetime.strptime(ts, R_PLACE_DATA_TIME_FMT_NO_MILS)
        ms_since_start = int((ts - R_PLACE_START_DT).total_seconds() * 1000)
        color_byte = R_PLACE_COLORS.index(color)
        uid = codecs.decode(bytes(uid, 'utf8'), 'base64')

        coords = list(map(int, coords.split(',')))
        # handle admin rectangles
        if len(coords) == 2:
            x, y = coords
            if self.with_uids:
                self.fileobj.write(R_PLACE_UID_PIXEL.pack(
                    ms_since_start, uid, color_byte, x, y
                ))
            else:
                self.fileobj.write(R_PLACE_ANON_PIXEL.pack(
                    ms_since_start, color_byte, x, y))
        elif len(coords) == 4:
            x1, y1, x2, y2 = coords
            for x in range(x1, x2+1):
                for y in range(y1, y2+1):
                    if self.with_uids:
                        self.fileoj.write(R_PLACE_UID_PIXEL.pack(
                            ms_since_start, uid, color_byte, x, y
                        ))
                    else:
                        self.fileobj.write(R_PLACE_ANON_PIXEL.pack(
                            ms_since_start, color_byte, x, y))

    def writerows(self, rows):
        for row in rows:
            self.write_row(row)


class Reader(object):
    def __init__(self, fileobj):
        self.fileobj = fileobj
        self.with_uids = self.fileobj.read(1) == b'\x01'

    def __next__(self):
        if self.with_uids:
            chunk = self.fileobj.read(R_PLACE_UID_PIXEL.size)
            if len(chunk) != R_PLACE_UID_PIXEL.size:
                raise StopIteration
            ms_since_start, uid, color_byte, x, y = R_PLACE_UID_PIXEL.unpack(
                chunk)
            uid = codecs.encode(uid, 'base64').decode('utf8').replace('\n', '')

        else:
            chunk = self.fileobj.read(R_PLACE_ANON_PIXEL.size)
            if len(chunk) != R_PLACE_ANON_PIXEL.size:
                raise StopIteration

            ms_since_start, color_byte, x, y = R_PLACE_ANON_PIXEL.unpack(chunk)
            uid = ANON_UID

        ts = R_PLACE_START_DT + timedelta(milliseconds=ms_since_start)
        color = R_PLACE_COLORS[color_byte]

        return ts, uid, color, x, y

    def __iter__(self):
        return self


class ReaderCsv(Reader):
    def __next__(self):
        ts, uid, color, x, y = super().__next__()
        return [ts.strftime(R_PLACE_DATA_TIME_FMT)[:-3] + ' UTC',
                uid,
                color,
                f'{x},{y}']


def hex_to_rgb(hex):
    return struct.unpack('BBB', codecs.decode(
        bytes(hex.lstrip('#'), 'utf8'), 'hex'))


class Canvas(object):
    def __init__(self, upper_left=(0, 0), lower_right=(2000, 2000)):
        self.upper_left = upper_left
        self.lower_right = lower_right

        self.pixels = [[(255, 255, 255)
                        for x in range(self.size[0])]
                       for y in range(self.size[1])]

    def apply_pixel(self, ts, x, y, color):
        x -= self.upper_left[0]
        y -= self.upper_left[1]

        if (x < self.size[0] and x >= 0) and (y < self.size[1] and y >= 0):
            self.pixels[y][x] = hex_to_rgb(color)

    @property
    def size(self):
        return (self.lower_right[0] - self.upper_left[0],
                self.lower_right[1] - self.upper_left[1])

    def from_image(self, img):
        flat_pixels = img.crop((
            self.upper_left[0],
            self.upper_left[1],
            self.lower_right[0],
            self.lower_right[1])).getdata()

        for x in range(self.size[0]):
            for y in range(self.size[1]):
                self.pixels[y][x] = flat_pixels[
                    (y * (self.size[1])) + x]

    def to_image(self):
        img = Image.new('RGB', self.size)
        flat_pixels = []
        for row in self.pixels:
            flat_pixels += row

        img.putdata(flat_pixels)

        return img
