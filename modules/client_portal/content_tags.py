"""Pulls inline content-tagged passages out of a report body.

The report editor wraps a tagged passage as
<span class="content-tag" data-tag-id="12" data-tag-name="Inflation">…</span>
inside an article block (<p>, <h2>, <blockquote>, stat-block <div>, …). This turns a
body into a flat list of passages, each with the surrounding block text as context, for
the client portal's Tagged Insights page.
"""
from html.parser import HTMLParser

BLOCK_TAGS = {'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'li', 'ul', 'ol', 'figure'}
CONTEXT_CHARS = 160


def _trim_before(text):
    text = ' '.join(text.split())
    if len(text) <= CONTEXT_CHARS:
        return text
    cut = text[-CONTEXT_CHARS:]
    return '… ' + cut[cut.find(' ') + 1:] if ' ' in cut else '… ' + cut


def _trim_after(text):
    text = ' '.join(text.split())
    if len(text) <= CONTEXT_CHARS:
        return text
    cut = text[:CONTEXT_CHARS]
    return (cut[:cut.rfind(' ')] if ' ' in cut else cut) + ' …'


class _TaggedPassageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.passages = []
        self._block_text = []
        self._open_passages = []  # passages started in the current block, not yet closed
        self._block_passages = []  # passages closed in the current block, awaiting context
        self._span_stack = []  # None for ordinary spans, a passage dict for content-tag spans
        self._block_stack = []  # open block elements, to know if a passage sits in a quote or heading

    def _block_len(self):
        return sum(len(chunk) for chunk in self._block_text)

    def _flush_block(self):
        text = ''.join(self._block_text)
        # A tag span left open at a block boundary (malformed HTML) ends with the block.
        for passage in self._open_passages:
            passage['end'] = len(text)
            self._block_passages.append(passage)
        self._open_passages = []
        self._span_stack = [None if isinstance(item, dict) else item for item in self._span_stack]

        if 'blockquote' in self._block_stack:
            kind = 'quote'
        elif any(tag in self._block_stack for tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')):
            kind = 'heading'
        else:
            kind = 'text'
        for passage in self._block_passages:
            passage_text = ' '.join(text[passage['start']:passage['end']].split())
            if not passage_text:
                continue
            self.passages.append({
                'tag_id': passage['tag_id'],
                'tag_name': passage['tag_name'],
                'text': passage_text,
                'before': _trim_before(text[:passage['start']]),
                'after': _trim_after(text[passage['end']:]),
                'kind': kind,
            })
        self._block_text = []
        self._block_passages = []

    def handle_starttag(self, tag, attrs):
        if tag in BLOCK_TAGS:
            self._flush_block()
            self._block_stack.append(tag)
        elif tag == 'br':
            self._block_text.append(' ')
        elif tag == 'span':
            attrs = dict(attrs)
            classes = (attrs.get('class') or '').split()
            if 'content-tag' in classes and (attrs.get('data-tag-id') or '').isdigit():
                passage = {
                    'tag_id': int(attrs['data-tag-id']),
                    'tag_name': attrs.get('data-tag-name') or '',
                    'start': self._block_len(),
                }
                self._open_passages.append(passage)
                self._span_stack.append(passage)
            else:
                self._span_stack.append(None)

    def handle_endtag(self, tag):
        if tag in BLOCK_TAGS:
            self._flush_block()
            if tag in self._block_stack:
                del self._block_stack[len(self._block_stack) - 1 - self._block_stack[::-1].index(tag):]
        elif tag == 'span' and self._span_stack:
            passage = self._span_stack.pop()
            if isinstance(passage, dict) and passage in self._open_passages:
                passage['end'] = self._block_len()
                self._open_passages.remove(passage)
                self._block_passages.append(passage)

    def handle_data(self, data):
        self._block_text.append(data)

    def close(self):
        super().close()
        self._flush_block()


def extract_tagged_passages(html):
    """Return [{tag_id, tag_name, text, before, after, kind}, …] in document order (kind: text/quote/heading)."""
    if not html or 'content-tag' not in html:
        return []
    parser = _TaggedPassageParser()
    parser.feed(html)
    parser.close()
    return parser.passages
