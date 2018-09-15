#!/usr/bin/env python3

import sys
import pprint
import urllib
import pathlib
import plistlib
import functools


def open_library_xml(library_path):
    library_xml_path = library_path / 'iTunes Library.xml'
    with library_xml_path.open('rb') as xml_file:
        return plistlib.load(xml_file)


def decode_location(s):
    path_part = urllib.parse.urlparse(s).path
    return urllib.parse.unquote(path_part)


@functools.total_ordering
class Track(object):
    def __init__(self, track):
        self.track_id = track['Track ID']
        self.album = track['Album']
        self.name = track['Name']

        self.album_artist = track.get('Album Artist', '???')
        self.track_number = track.get('Track Number', -1)
        self.location = decode_location(track.get('Location', ''))

        self._compare_value = (
            self.album_artist,
            self.album,
            self.track_number,
            self.name,
            self.track_id
        )

    def file_exists(self):
        return self.location and pathlib.Path(self.location).exists()

    def __eq__(self, other):
        return self._compare_value == other._compare_value

    def __lt__(self, other):
        return self._compare_value < other._compare_value


def filter_missing_tracks(tracks):
    return [track for track in tracks if not track.file_exists()]


def print_missing_tracks(missing_tracks):
    pprint.pprint([
        '{} / {} / ({}) {}'.format(track.album_artist, track.album, track.track_number, track.name)
        for track in sorted(missing_tracks)
    ])
    print('Total: {}'.format(len(missing_tracks)))


def main(args):
    if len(args) < 1:
        print('Call with library path!')
        return

    library_root = pathlib.Path(args[0]).expanduser().resolve()

    library = open_library_xml(library_root)
    tracks = [Track(plist_object) for plist_object in library['Tracks'].values()]

    missing_tracks = filter_missing_tracks(tracks)
    print_missing_tracks(missing_tracks)


if __name__ == '__main__':
    main(sys.argv[1:])
