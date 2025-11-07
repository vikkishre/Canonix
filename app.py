# app.py
from flask import Flask, render_template, request, jsonify
import re

app = Flask(__name__)

def relaxed_header_canonicalize(raw_header):
    """
    Robust DKIM relaxed header canonicalization.
    - Accepts raw strings that may contain literal "\\r\\n" sequences.
    - Normalizes newlines to CRLF, unfolds continuations, lowercases names,
      collapses WSP in values, and returns headers joined with CRLF ending.
    """
    if raw_header is None:
        return '\r\n'

    # 0) If input contains literal backslash-r backslash-n sequences (common when
    # passing headers as a single-line JSON string), turn those into actual CRLF.
    raw_header = raw_header.replace('\\r\\n', '\r\n').replace('\\n', '\r\n')

    # 1) Normalize any lone LF or CR to CRLF so we have a consistent newline form
    raw_header = raw_header.replace('\r\n', '\n').replace('\r', '\n')  # unify to '\n'
    raw_header = raw_header.replace('\n', '\r\n')                    # convert to CRLF

    # 2) Unfold continuation lines: replace CRLF followed by WSP with single SP
    unfolded = re.sub(r'(\\t|\\r\\n[ \t]+|\r\n[ \t]+)', ' ', raw_header)

    # 3) Split into lines (now no folding)
    lines = [line for line in unfolded.split('\r\n') if line != '']

    canon_fields = []
    for line in lines:
        # find the first colon separating name and value
        colon_pos = line.find(':')
        if colon_pos == -1:
            # skip malformed header lines with no colon
            continue

        # header-name: lowercase, trim WSP around it
        name = line[:colon_pos].strip().lower()

        # header-value: collapse WSP and strip
        value = line[colon_pos + 1:]
        value = re.sub(r'[ \t]+', ' ', value).strip()

        canon_fields.append(f"{name}:{value}")

    # join with CRLF and ensure a single CRLF at end
    return '\r\n'.join(canon_fields) + '\r\n'



def relaxed_body_canonicalize(raw_body):
    """DKIM Relaxed Body Canonicalization (RFC 6376 §3.4.2)"""
    lines = raw_body.splitlines()
    canon_lines = []

    for line in lines:
        # Remove trailing whitespace
        line = line.rstrip(' \t')
        # Collapse internal WSP to single space
        line = re.sub(r'[ \t]+', ' ', line)
        canon_lines.append(line)

    # Remove trailing empty lines
    while canon_lines and not canon_lines[-1]:
        canon_lines.pop()

    # If body is empty, canonical form is a single CRLF
    if not canon_lines:
        return '\r\n'

    return '\r\n'.join(canon_lines) + '\r\n'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/canonicalize', methods=['POST'])
def canonicalize():
    data = request.json
    header = data.get('header', '')
    body = data.get('body', '')

    return jsonify({
        'header': relaxed_header_canonicalize(header),
        'body': relaxed_body_canonicalize(body)
    })


if __name__ == '__main__':
    app.run(debug=True)