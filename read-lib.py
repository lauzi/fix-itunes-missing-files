#!/usr/bin/env python3

import sys
import pprint
import urllib
import pathlib
import plistlib
import functools

# pip install appscript
import mactypes
import appscript

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

    def __str__(self):
        return '#{}: {} / {}'.format(self.track_id, self.album, self.name)

    def __repr__(self):
        return repr({
            'Track ID': self.track_id,
            'Album Artist': self.album_artist,
            'Album': self.album,
            'Track No.': self.track_number,
            'Title': self.name,
            'Location': self.location
        })

    def find_location(self, directory_tree):
        if not self.location:
            return ''

        if self.file_exists():
            return pathlib.Path(self.location)

        # Can use difflib but it's slow and not really better
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


def get_itunes_library():
    app = appscript.app('iTunes')
    playlists = app.library_playlists.get()

    if len(playlists) != 1:
        raise Exception('There are {} libraries!'.format(len(playlists)))

    return playlists[0]


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
    renames = []
    for track in missing_tracks:
        actual_path = track.find_location(directory_tree)
        if actual_path:
            renames.append((track, actual_path))

    if '-v' in args:
        with open('old.txt', 'w') as old_f:
            with open('new.txt', 'w') as new_f:
                for track, actual_path in renames:
                    old_f.write(track.location + '\n')
                    new_f.write(actual_path.as_posix() + '\n')
        print('Wrote old.txt, new.txt to use with vimdiff')
        return

    lib = get_itunes_library()
    num_success = 0
    failures = []
    for track, actual_location in renames:
        matching_tracks = lib.tracks[appscript.its.database_ID == track.track_id].get()
        if len(matching_tracks) != 1:
            print('Failed to find track {} in iTunes!'.format(track))
            failures.append(track)
            continue
        track_meta = matching_tracks[0]
        track_meta.location.set(mactypes.Alias(actual_location))

        print(track, ' -> ', actual_location)
        num_success += 1

    print('Succeeded: {}'.format(num_success))
    print('GG: ')
    pprint.pprint(failures)


if __name__ == '__main__':
    main(sys.argv[1:])
