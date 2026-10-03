# Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
import unittest
from server.plex_api import public_ratings


class RatingTests(unittest.TestCase):
    def test_providers_and_deduplication(self):
        result = public_ratings({'Rating': [
            {'image': 'imdb://image.rating', 'value': 6.3},
            {'image': 'rottentomatoes://image.rating.ripe', 'value': 6.6, 'type': 'critic'},
            {'image': 'rottentomatoes://image.rating.upright', 'value': 6.3, 'type': 'audience'}],
            'rating': 6.6, 'ratingImage': 'rottentomatoes://image.rating.ripe'})
        self.assertEqual(result, [{'label': 'IMDb', 'score': '6.3/10'},
            {'label': 'Rotten Tomatoes critics', 'score': '66%'},
            {'label': 'Rotten Tomatoes audience', 'score': '63%'}])

    def test_fallback_and_missing(self):
        self.assertEqual(public_ratings({'rating': 7}), [{'label': 'Plex rating', 'score': '7.0/10'}])
        self.assertEqual(public_ratings({}), [])
        self.assertEqual(public_ratings({'audienceRating': 0,
            'audienceRatingImage': 'rottentomatoes://image.rating.spilled'}),
            [{'label': 'Rotten Tomatoes audience', 'score': '0%'}])

    def test_invalid_values(self):
        for value in [None, 'bad', float('nan'), float('inf'), -1, 11, True]:
            self.assertEqual(public_ratings({'rating': value}), [])
        self.assertEqual(public_ratings({'Rating': [None,
            {'value': 7, 'image': 'https://untrusted/icon'}]}), [])
