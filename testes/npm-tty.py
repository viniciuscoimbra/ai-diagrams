"""Exercise real terminal confirmation and rollback using only temporary files."""
import os
from pathlib import Path
import pty
import select
import subprocess
import sys
import time

node, cli, folder = sys.argv[1:]
tmp = Path(folder)
assert Path(os.environ['HOME']) == tmp / 'home'


def interact(args, answer, env=None):
    master, slave = pty.openpty()
    child = subprocess.Popen([node, cli, *args], stdin=slave, stdout=slave, stderr=slave,
                             env=env, cwd=tmp)
    os.close(slave)
    output = b''
    replied = False
    deadline = time.monotonic() + 10
    try:
        while time.monotonic() < deadline:
            if select.select([master], [], [], 0.1)[0]:
                try:
                    chunk = os.read(master, 65536)
                except OSError:
                    break
                if not chunk:
                    break
                output += chunk
                if b'[s/N]' in output and not replied:
                    os.write(master, (answer + '\n').encode())
                    replied = True
            elif child.poll() is not None:
                break
        assert replied, output.decode()
        return child.wait(timeout=2), output.decode()
    finally:
        os.close(master)
        if child.poll() is None:
            child.kill()
            child.wait()


project = tmp / 'interactive project'
dest = project / '.claude/skills/ai-diagrams'
dest.mkdir(parents=True)
(dest / 'keep.txt').write_text('original')
args = ['install', '--claude', '--projeto', project.name]
status, output = interact(args, 'n')
assert status == 1, output
assert (dest / 'keep.txt').read_text() == 'original'
status, output = interact(args, 's')
assert status == 0, output
assert dest.is_symlink()
assert (dest / 'SKILL.md').is_file()
assert 'Backup preservado:' in output
backups = list(dest.parent.glob('.ai-diagrams-backup-*/original/keep.txt'))
assert len(backups) == 1 and backups[0].read_text() == 'original'

kiro = tmp / 'project kiro'
before = {str(p.relative_to(kiro)): p.read_bytes() for p in kiro.rglob('*') if p.is_file()}
fakebin = tmp / 'failing-bin'
fakebin.mkdir()
bash = fakebin / 'bash'
bash.write_text('#!/bin/sh\nexit 7\n')
bash.chmod(0o755)
status, output = interact(['install', '--kiro', '--projeto', str(kiro)], 's',
                         dict(os.environ, PATH=str(fakebin)))
assert status == 1 and 'falhou (7)' in output, output
after = {str(p.relative_to(kiro)): p.read_bytes() for p in kiro.rglob('*') if p.is_file()}
assert after == before, 'Kiro rollback must preserve every original file'
assert not list(kiro.rglob('.ai-diagrams-backup-*')), 'Rollback must not leak empty backups'
print('OK npm TTY: decline, confirmed replacement with backup, relative path with spaces and Kiro failure rollback.')
