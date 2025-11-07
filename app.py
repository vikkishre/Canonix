# app.py
from flask import Flask, render_template, request, jsonify
import re

app = Flask(__name__)

def relaxed_header_canonicalize(raw_header):
    """DKIM Relaxed Header Canonicalization (RFC 6376 §3.4.2)"""
    past_field_name = False
    seen_wsp = False
    eat_wsp = False
    relaxed = []

    for c in raw_header:
        if c in '\r\n':
            continue
        elif c in ' \t':
            if not eat_wsp:
                seen_wsp = True
        else:
            if seen_wsp:
                relaxed.append(' ')
                seen_wsp = False
            if c == ':' and not past_field_name:
                past_field_name = True
                eat_wsp = True
            else:
                eat_wsp = False
            relaxed.append(c.lower() if not past_field_name else c)

    if seen_wsp:
        relaxed.append(' ')

    result = ''.join(relaxed).strip()
    colon_pos = result.find(':')
    if colon_pos != -1:
        name = result[:colon_pos].rstrip()
        value = result[colon_pos + 1:].lstrip()
        result = name + ':' + value

    return result + '\r\n'

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