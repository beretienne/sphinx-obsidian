"""Process wikilinks"""
import re
import os
from typing import Any, Callable, Dict, Optional

from markdown_it import MarkdownIt
from markdown_it.rules_inline import StateInline
from markdown_it.common.utils import isSpace
from markdown_it import ruler
from sphinx_obsidian import helpers


# VALID_WIKI_PATTERN = re.compile(r"\[\[([^\]\[]+)\]\]")
# VALID_WIKI_PATTERN = re.compile(r'\[\[([^\]\[\:\|]+)\]\]')
# FILENAME = re.compile(r'^(?:.*\/)*([^\/\r\n]+?|)(?=(?:\.[^\/\r\n.]*)?$)')

def wikilinks_plugin(md: MarkdownIt) -> None:
    """Plugin to parse wikilink type links

    It parses URI's stored between /* [[...]] */

    .. code-block:: md

        [[wikilink]]

    """
#    frontMatter = make_front_matter_rule()
    md.inline.ruler.before(
        "link",
        "wikilink",
        wikilink,
    )


def wikilink(state: StateInline, silent: bool) -> bool:

    href = ""
    label = None
    oldPos = state.pos
    maximum = state.posMax
    start = state.pos
    pos = start
    parseReference = True

    if state.srcCharCode[state.pos] != 0x5B:  # /* [ */
        return False
    pos += 1
    if state.srcCharCode[state.pos] != 0x5B:  # /* [ */
        return False
    # [[  <href>  | link label ]]
    #   ^^ skipping these spaces
    pos += 1
    while pos < maximum:
        code = state.srcCharCode[pos]
        if not isSpace(code) and code != 0x0A:
            break
        pos += 1

    if pos >= maximum:
        return False

    # [[  <href>  | link label ]]
    #     ^^^^^^ parsing link destination
    res = helpers.parseLinkDestination(state.src, pos, state.posMax)
    if res.ok:
        # might have found a valid shortcut link, disable reference parsing
        parseReference = False
        href = state.md.normalizeLink(res.str)
        if state.md.validateLink(href):
            pos = res.pos
        else:
            href = ""
            # start = pos -> TO BE CHECKED
        # [[  <href>  | link label ]]
        #           ^^ skipping these spaces
        while pos < maximum:
            code = state.srcCharCode[pos]
            if not isSpace(code) and code != 0x0A:
                break
            pos += 1
        # valid link found
        state.pos = labelStart = labelEnd = pos
        if (code == 0x7C): # |
            labelEnd = helpers.parseLinkLabel(state, state.pos)
            # parser failed to find ']', so it's not a valid link label
            if labelEnd < 0:
                return False
        else:
            pass # no label has been found
            
            pos = labelEnd + 1
    else:
        parseReference = True

    if parseReference:
        #
        # Link reference
        #
        if "references" not in state.env:
            return False

        if pos < maximum and state.srcCharCode[pos] == 0x5B:  # /* [ */
            start = pos + 1
            pos = state.md.helpers.parseLinkLabel(state, pos)
            if pos >= 0:
                label = state.src[start:pos]
                pos += 1
            else:
                pos = labelEnd + 1

        else:
            pos = labelEnd + 1

        # covers label == '' and label == undefined
        # (collapsed reference link and shortcut reference link respectively)
        if not label:
            label = state.src[labelStart:labelEnd]

        label = normalizeReference(label)

        ref = (
            state.env["references"][label] if label in state.env["references"] else None
        )
        if not ref:
            state.pos = oldPos
            return False

        href = ref["href"]
        title = ref["title"]

    #
    # We found the end of the link, and know for a fact it's a valid link
    # so all that's left to do is to call tokenizer.
    
    if not silent:
        state.pos = labelStart
        state.posMax = labelEnd

        token = state.push("link_open", "a", 1)
        token.attrs = {"href": href}

        # note, this is not part of markdown-it JS, but is useful for renderers
        if label and state.md.options.get("store_labels", False):
            token.meta["label"] = label

#        state.md.inline.tokenize(state)

        token = state.push("link_close", "a", -1)

    state.pos = state.posMax
    state.posMax = maximum
    return True
