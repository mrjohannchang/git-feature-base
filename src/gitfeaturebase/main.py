# -*- coding: utf-8 -*-

import argparse
import os
import re
import shlex
import subprocess
import sys


class PatchInfo:
    def __init__(self, filename, patch, is_establishment):
        self.filename = filename
        self.patch = patch
        self.is_establishment = is_establishment

def run_cmd(cmd):
    p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    return p.stdout.read()

def get_args():
    args_parser = argparse.ArgumentParser(
            prog='git feature-base',
            description='List dependent commits against the given range.')

    args_parser.add_argument(
            'start_point',
            metavar = 'commit',
            help='the start commit')

    args_parser.add_argument(
            'end_point',
            metavar = 'commit',
            nargs = '?',
            default = 'HEAD',
            help='the end commit')

    args_parser.add_argument(
            '-a', '--all',
            action='store_true',
            help='show the whole related patches')

    args = args_parser.parse_args()
    return args

def chdir_to_git_root():
    if not os.path.exists('.git'):
        os.chdir(os.path.dirname(os.getcwd()))
        chdir_to_git_root()

def get_diff(start_point, end_point):
    cmd = 'git diff {start_point}'.format(start_point=start_point)
    if end_point:
        cmd += ' {end_point}'.format(end_point=end_point)
    return run_cmd(cmd)

def split_diff(diff):
    sep = 'diff --git a/'
    patches = diff.split(sep)
    patches.pop(0)

    filenames = list()
    for p in patches:
        filename, sep, not_insterested = p.partition(' b/')
        filenames.append(filename)
    return patches, filenames

def get_patches(diff):
    patches = list()
    ps, fs = split_diff(diff)
    for p, f in zip(ps, fs):
        patches.append(PatchInfo(f, p, not os.path.exists(f)))
    return patches

def get_last_commit_of_file(filename, boundary):
    commit = ''

    if boundary:
        cmd = 'git log -1 --pretty=%H {boundary}^ -- {filename}'.format(
                boundary=boundary, filename=filename)
    else:
        cmd = 'git log -1 --pretty=%H -- {filename}'.format(filename=filename)

    return run_cmd(cmd).rstrip()

def _get_related_commits(patch, start_point):
    raw_patch_lines = patch.patch.splitlines()

    line_descriptors = list()
    for l in raw_patch_lines:
        if re.match('^@@\ -.+\+.*\ @@.*', l):
            line_descriptors.append(l)

    related_lines = list()
    for l in line_descriptors:
        l = re.sub('^@@\ -', '', l)
        l = re.sub('\ \+.*', '', l)
        related_lines.append(l)

    blames = list()
    if not start_point:
        start_point = 'HEAD'
    blames = run_cmd('git blame {start_point} -l -- {filename}'.format(
        start_point=start_point, filename=patch.filename)).splitlines()

    commits = list()
    for b in blames:
        b = b.split(' ')[0]
        if b.startswith('^'):
            b = b[1:]
        commits.append(b)

    releated_commits = list()
    for line_descriptor in related_lines:
        line_num, count = map(int, line_descriptor.split(','))
        for i in xrange(line_num - 1, line_num - 1 + count):
            releated_commits.append(commits[i])
    return set(releated_commits)

def sort_commits_by_date(commits):
    sorted_commits = list()
    for c in commits:
        sha1, commit_time = run_cmd("git log -1 --pretty='%H %ct' {commit}" \
                .format(commit=c)).rstrip().split(' ')
        sorted_commits.append((sha1, commit_time))
    sorted_commits.sort(key = lambda tup: tup[1])
    return [commit for commit, time in sorted_commits]

def is_commit_linked(commit1, commit2):
    p1 = subprocess.Popen(
            shlex.split('git merge-base --is-ancestor {commit1} {commit2}' \
                    .format(commit1=commit1, commit2=commit2)))
    p1 = subprocess.Popen(
            shlex.split('git merge-base --is-ancestor {commit2} {commit1}' \
                    .format(commit1=commit1, commit2=commit2)))
    if p1.wait() and p2.wait():
        return False
    return True

def get_related_commits(patches, start_point, end_point):
    commits = list()

    for p in patches:
        if p.is_establishment:
            commits.append(get_last_commit_of_file(p.filename, end_point))
            continue
        commits.extend(_get_related_commits(p, start_point))

    return reversed(sort_commits_by_date(set(commits)))

def print_result(args, commits):
    if not commits: return

    for c in commits:
        print(c, end=' ')
        print(run_cmd("git log -1 --pretty='%ci %an <%ae>' {commit}".format(
            commit=c)).rstrip())
        if not args.all: break

def is_ancestor(start_point, end_point):
    p = subprocess.Popen(shlex.split(
        'git merge-base --is-ancestor {start_point} {end_point}'.format(
            start_point=start_point, end_point=end_point)))
    return not p.wait()

def is_clean():
    return not run_cmd('git status --porcelain')

def init(args):
    if not is_clean():
        print('Error: status not clean', file=sys.stderr)
        exit(1)

    if not is_ancestor(args.start_point, args.end_point):
        print('Error: {start_point} is not an ancestor of {end_point}' \
                .format(start_point=args.start_point, end_point=args.end_point),
                file=sys.stderr)
        exit(1)

def main():
    args = get_args()
    chdir_to_git_root()
    init(args)
    diff = get_diff(args.start_point, args.end_point)
    patches = get_patches(diff)
    releated_commits = get_related_commits(patches, args.start_point,
            args.end_point)
    print_result(args, releated_commits)

if __name__ == '__main__':
    main()
