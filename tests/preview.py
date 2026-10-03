# Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
"""Optional browser fixture, loopback only: python -m tests.preview."""
from server.app import create_app


class PreviewPlex:
    def libraries(self):
        return [{'id': '1', 'title': 'Test Movies', 'type': 'movie'}]

    def items(self, section):
        return [self.metadata(str(i)) for i in range(1, 21)]

    def library_page(self, section, offset=0, sort="title"):
        return {'items': [self.metadata(str(54 - i if sort == "recent" else i)) for i in range(offset + 1, min(offset + 21, 54))],
                'offset': offset, 'total': 53, 'previous': offset - 20 if offset else None,
                'next': offset + 20 if offset + 20 < 53 else None}

    def metadata(self, key):
        return {'id': key, 'title': 'Test Movie ' + key, 'type': 'movie', 'year': 2026,
                'duration': 7200000, 'rating': 8.0, 'summary': 'Local fixture for testing TV navigation and details.',
                'cast': ['Test Actor'], 'poster': None, 'background': None}

    def public(self, item):
        return item

    def feed(self, name):
        entries = self.items('1')
        if name == 'continue':
            for entry in entries[:3]:
                entry['viewOffset'] = 3600000
            entries = entries[:3]
        return {'items': entries}

    def watchlist(self):
        return {'items': self.items('1')[:4], 'truncated': False}


if __name__ == '__main__':
    from waitress import serve
    serve(create_app(client=PreviewPlex()), host='127.0.0.1', port=8766)
