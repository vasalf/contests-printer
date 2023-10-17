#!/usr/bin/python3

from flask import Flask, Response, abort
from flask_httpauth import HTTPBasicAuth

import os
import json


app = Flask(__name__)
auth = HTTPBasicAuth()


def problem_letter(filename):
    if ord('A') <= ord(filename[0]) and ord(filename[0]) <= ord('Z'):
        return filename[0]
    return None


def load_contest(path):
    files = [ f for f in os.scandir(path) if f.is_file() and f.name.endswith(".cpp") ]
    files.sort(key=lambda f : f.name)

    contest = dict()
    for f in files:
        c = problem_letter(f.name)
        if c not in contest:
            contest[c] = []
        contest[c].append(f)

    return contest


def load_contests(contests_path):
    dirs = [ d for d in os.scandir(contests_path) if d.is_dir() ]
    dirs.sort(key=lambda d:d.name)
    return [ (d, load_contest(d)) for d in dirs ]


def max_letter(contests):
    max_letter = chr(ord('A') - 1)
    for d, contest in contests:
        for c, files in contest.items():
            if c is not None:
                max_letter = chr(max(ord(max_letter), ord(c)))
    return max_letter


def table_header(max_letter):
    ret = "<thead><tr>"
    ret += '<th scope="col">Name</th>'
    for i in range(ord('A'), ord(max_letter) + 1):
        ret += '<th scope="col">' + chr(i) + "</th>"
    ret += '<th scope="col">Other files</th>'
    ret += "</tr></thead>"
    return ret


def problem_link(d, f):
    return f'<a href="{path_prefix}/{d.name}/{f.name}">{f.name}</a>'


def table_body(contests, max_letter):
    ret = "<tbody>"
    for d, contest in contests:
        ret += "<tr>"
        ret += '<th scope="row">' + d.name + "</th>"
        for i in range(ord('A'), ord(max_letter) + 1):
            ret += "<td>"
            if chr(i) in contest:
                ret += " ".join(map(lambda f: problem_link(d, f), contest[chr(i)]))
            ret += "</td>"
        ret += "<td>"
        if None in contest:
            ret += " ".join(map(lambda f: problem_link(d, f), contest[None]))
        ret += "</td>"
        ret += "</tr>"
    ret += "</tbody>"
    return ret


def table(contests):
    l = max_letter(contests)
    ret = '<table class="table table-striped">'
    ret += table_header(l)
    ret += table_body(contests, l)
    ret += "</table>"
    return ret


def html_head():
    ret = "<head>"
    ret += '<meta charset="utf-8">'
    ret += '<meta name="viewport" content="width=device-width, initial-scale=1">'
    ret += "<title>Printer</title>"
    ret += '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-T3c6CoIi6uLrA9TneNEoa7RxnatzjcDSCmG1MXxSR1GAsXEV/Dwwykc2MPK8M2HN" crossorigin="anonymous">'
    ret += "</head>"
    return ret


def html_body(contests):
    ret = "<body>"
    ret += '<div class="container">'
    ret += table(contests)
    ret += '</div>'
    ret += "</body>"
    return ret


def load_config():
    global contests_root
    global users
    global path_prefix
    with open('/etc/contests-printer/config.json') as fin:
        config = json.load(fin)
        contests_root = config['contests_root']
        users = config['users']
        path_prefix = config['path_prefix']


load_config()


@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username


@app.route(path_prefix)
@auth.login_required
def root():
    contests = load_contests(contests_root)
    answer = "<!doctype html>"
    answer += "<html>"
    answer += html_head()
    answer += html_body(contests)
    answer += "</html>"
    return answer


@app.route(f"{path_prefix}<contest_name>/<filename>")
@auth.login_required
def get(contest_name, filename):
    contests = load_contests(contests_root)
    contest = None
    for d, c in contests:
        if d.name == contest_name:
            contest = c
    if contest is None:
        abort(404)
    file = None
    for l, files in contest.items():
        for f in files:
            if f.name == filename:
                file = f
    if file is None:
        abort(404)
    with open(file, 'r') as fin:
        return Response(str(fin.read()), mimetype='text/plain')

