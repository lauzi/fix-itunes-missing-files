#!/usr/bin/env python3

import sys
import pprint
import urllib
import pathlib
import plistlib
import functools

# pip install editdistance
import editdistance


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

    def find_location(self, directory_tree):
        if not self.location:
            return ''

        if self.file_exists():
            return pathlib.Path(self.location)

        return min(directory_tree, key=lambda p: editdistance.eval(self.location, p.as_posix()))


def filter_missing_tracks(tracks):
    return [track for track in tracks if not track.file_exists()]


def print_missing_tracks(missing_tracks):
    pprint.pprint([
        '{} / {} / ({}) {}'.format(track.album_artist, track.album, track.track_number, track.name)
        for track in sorted(missing_tracks)
    ])
    print('Total: {}'.format(len(missing_tracks)))


def get_directory_tree(library_root):
    return list(pathlib.Path(library_root / 'iTunes Media' / 'Music').glob('**/*.mp3'))


def main(args):
    if len(args) < 1:
        print('Call with library path!')
        return

    library_root = pathlib.Path(args[0]).expanduser().resolve()
    directory_tree = get_directory_tree(library_root)

    library = open_library_xml(library_root)
    tracks = [Track(plist_object) for plist_object in library['Tracks'].values()]

    missing_tracks = filter_missing_tracks(tracks)

    missing_tracks.sort()
    for track in missing_tracks:
        actual_path = track.find_location(directory_tree)
        if actual_path:
            print('{} -> {}'.format(track.location, actual_path))


if __name__ == '__main__':
    main(sys.argv[1:])
