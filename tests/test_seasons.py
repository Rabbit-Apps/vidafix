# Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
import unittest
from unittest.mock import Mock
from server.app import create_app
from server.plex_api import PlexClient

class SeasonTests(unittest.TestCase):
    def setUp(self):
        self.plex=PlexClient('http://127.0.0.1:32400','fixture')
        self.plex.metadata=Mock(return_value={'type':'show'})
        self.plex.fetch=Mock(return_value={'Metadata':[{'ratingKey':'12','type':'season','title':'Season 1','thumb':'/library/metadata/12/thumb/9'}]})
        self.client=create_app(client=self.plex).test_client()
    def test_seasons_use_children_and_own_art(self):
        result=self.client.get('/api/show/1/seasons').get_json()
        self.assertEqual(result['items'][0]['poster'],'/art/12/thumb')
        self.assertEqual(self.plex.fetch.call_args.args[0],'/library/metadata/1/children')
        self.plex.metadata.return_value={'type':'season','thumb':'/library/metadata/12/thumb/9','grandparentThumb':'/library/metadata/1/thumb/3'}
        self.plex.artwork('12','thumb')
        self.plex.fetch.assert_called_with('/library/metadata/12/thumb/9',image=True)
    def test_episode_parent_and_paging(self):
        self.assertEqual(self.client.get('/api/season/12/episodes').status_code,400)
        self.plex.metadata.return_value={'type':'season'}
        self.plex.fetch.return_value={'Metadata':[{'ratingKey':str(i),'type':'episode','title':'Episode'} for i in range(20)],'totalSize':24}
        data=self.client.get('/api/season/12/episodes').get_json()
        self.assertEqual(data['next'],20)
        self.assertEqual(self.plex.fetch.call_args.args[0],'/library/metadata/12/children')
        self.assertEqual(self.client.get('/api/season/12/episodes?offset=1').status_code,400)
