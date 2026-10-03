# Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
import unittest
from unittest.mock import patch
from server.plex_api import PlexClient, PlexError


def item(key, kind='movie', section='1', **extra):
    return dict(ratingKey=str(key), type=kind, librarySectionID=section, title='Local title', **extra)


class FeedTests(unittest.TestCase):
    def setUp(self):
        self.plex = PlexClient('http://127.0.0.1:32400', 'secret')
        self.libraries = patch.object(self.plex, 'libraries', return_value=[
            {'id': '1', 'type': 'movie'}, {'id': '2', 'type': 'show'}, {'id': '3', 'type': 'movie'}])
        self.libraries.start()
        self.addCleanup(self.libraries.stop)

    def test_continue_only_local_in_progress(self):
        data = {'Hub': [{'hubIdentifier': 'continueWatching', 'Metadata': [
            item(1, viewOffset=100), item(2, 'episode', '2'),
            item(3, section='99', viewOffset=100), item(4, 'track', viewOffset=100)]}]}
        with patch.object(self.plex, 'fetch', return_value=data):
            self.assertEqual([x['id'] for x in self.plex.feed('continue')['items']], ['1'])

    def test_ondeck_excludes_started_watched_and_duplicates(self):
        rows = [item(1, 'episode', '2'), item(2, 'episode', '2', viewOffset=5),
                item(3, 'episode', '2', viewCount=1), item(4)]
        with patch.object(self.plex, 'fetch', return_value={'Metadata': rows}):
            self.assertEqual([x['id'] for x in self.plex.feed('ondeck')['items']], ['1'])

    def test_recent_global_sort_cap_and_type(self):
        with patch.object(self.plex, 'fetch', side_effect=[
            {'Metadata': [item(i, addedAt=i) for i in range(100)]},
            {'Metadata': [item(130, addedAt=130), item(131, 'track', addedAt=131)]}]):
            result = self.plex.feed('recent-movies')['items']
            self.assertEqual(len(result), 100)
            self.assertEqual(result[0]['id'], '130')

    def test_home_rows_cap_at_100(self):
        for name in ('continue', 'ondeck', 'recent-tv'):
            with self.subTest(name=name):
                entries = [item(i, 'episode', '2', addedAt=i,
                                viewOffset=10 if name == 'continue' else 0) for i in range(125)]
                with patch.object(self.plex, 'fetch', return_value={'Metadata': entries}) as fetch:
                    result = self.plex.feed(name)['items']
                    self.assertEqual(len(result), 100)
                    self.assertEqual(len({x['id'] for x in result}), 100)
                    self.assertTrue(all(call.args[1]['X-Plex-Container-Size'] == 100
                                        for call in fetch.call_args_list))
                    if name == 'recent-tv':
                        self.assertEqual(result[0]['id'], '124')
                        self.assertEqual(result[-1]['id'], '25')

    def test_episode_details_and_show_artwork(self):
        episode = item(5, 'episode', '2', grandparentTitle='Series', parentIndex=2, index=3,
                       grandparentThumb='/library/metadata/8/thumb/1')
        with patch.object(self.plex, 'fetch', return_value={'Metadata': [episode]}):
            result = self.plex.public(self.plex.metadata('5'))
            self.assertEqual(result['title'], 'Series')
            self.assertEqual(result['episodeTitle'], 'Local title')
        with patch.object(self.plex, 'metadata', return_value=episode), patch.object(self.plex, 'fetch') as fetch:
            self.plex.artwork('5', 'thumb')
            fetch.assert_called_once_with('/library/metadata/8/thumb/1', image=True)

    def test_watchlist_matches_exact_local_identity_not_title_or_cloud_id(self):
        online = [dict(guid='plex://movie/abc', type='movie', ratingKey='cloud', title='Cloud title'),
                  dict(guid='plex://movie/def', type='movie')]
        with patch.object(self.plex, '_request', return_value={'Metadata': online}) as cloud, \
             patch.object(self.plex, 'fetch', side_effect=[{'Metadata': [
                 item(1, guid='plex://movie/wrong'), item(2, section='99', guid='plex://movie/abc'),
                 item(3, guid='plex://movie/abc')]}, {'Metadata': []}]):
            result = self.plex.watchlist()
            self.assertEqual([x['id'] for x in result['items']], ['3'])
            self.assertEqual(result['items'][0]['title'], 'Local title')
            self.assertEqual(cloud.call_args.args[0], 'https://discover.provider.plex.tv/library/sections/watchlist/all')
            self.assertEqual(self.plex.watchlist(), result)
            self.assertEqual(cloud.call_count, 1)

    def test_watchlist_pagination_and_empty(self):
        with patch.object(self.plex, '_request', side_effect=[{'Metadata': [{'type': 'track'}] * 50}, {'Metadata': []}]) as cloud:
            self.assertEqual(self.plex.watchlist()['items'], [])
            self.assertEqual(cloud.call_args.args[1]['X-Plex-Container-Start'], 50)

    def test_watchlist_failure_is_not_empty_success(self):
        with patch.object(self.plex, '_request', side_effect=PlexError('Plex timed out.', 504)):
            with self.assertRaises(PlexError):
                self.plex.watchlist()
            self.assertIsNone(self.plex._watchlist_cache)

    def test_invalid_feed(self):
        with self.assertRaises(PlexError):
            self.plex.feed('discover')

    def test_recent_library_uses_selected_library_only(self):
        with patch.object(self.plex, 'fetch', return_value={'Metadata': [
                item(1, 'episode', '2', addedAt=1), item(2, 'episode', '2', addedAt=3), item(3)]}) as fetch:
            result = self.plex.recent_library('2')
            self.assertEqual([x['id'] for x in result['items']], ['2', '1'])
            self.assertEqual(fetch.call_args.args[0], '/library/sections/2/all')
            self.assertEqual(fetch.call_args.args[1]['type'], 4)
            self.assertEqual(fetch.call_args.args[1]['sort'], 'addedAt:desc')
        with self.assertRaises(PlexError):
            self.plex.recent_library('99')

    def test_more_than_three_custom_libraries(self):
        self.libraries.stop()
        data = {'Directory': [{'key': str(i), 'title': 'Custom ' + str(i), 'type': 'movie'} for i in range(7)]}
        with patch.object(self.plex, 'fetch', return_value=data):
            result = self.plex.libraries()
            self.assertEqual(len(result), 7)
            self.assertEqual(result[-1]['title'], 'Custom 6')
