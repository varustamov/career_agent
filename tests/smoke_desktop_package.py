"""Exercise the packaged launcher and dashboard on the package's target OS."""
import argparse
import json
import os
import signal
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def launch(executable, database, output):
    with socket.socket() as reserve:
        reserve.bind(('127.0.0.1', 0))
        port = reserve.getsockname()[1]
    env = {
        **os.environ,
        'CAREER_DB_PATH': str(database),
        'CAREER_PORT': str(port),
        'CAREER_SERVER_MODE': '0',
    }
    with output.open('w+b') as log:
        process = subprocess.Popen(
            [str(executable), '--no-browser'],
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=os.name != 'nt',
        )
        try:
            yield process, f'http://127.0.0.1:{port}'
        except Exception:
            log.seek(0)
            print(log.read().decode(errors='replace'))
            raise
        finally:
            if process.poll() is None:
                if os.name == 'nt':
                    # The single-file Windows bootloader launches a child process.
                    subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], check=True)
                else:
                    os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=15)


OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def request(origin, path, body=None, token=None):
    headers = {}
    if body is not None:
        body = json.dumps(body).encode()
        headers = {'Content-Type': 'application/json', 'Origin': origin, 'X-Career-Token': token}
    return OPENER.open(urllib.request.Request(origin + path, body, headers), timeout=2)


def wait_until_ready(process, origin):
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f'Desktop launcher exited during startup ({process.returncode})')
        try:
            with request(origin, '/api/runtime') as response:
                assert json.load(response) == {'server_mode': False}
            return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.25)
    raise TimeoutError('Desktop dashboard did not start within 60 seconds')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    executable = parser.parse_args().executable.resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix='career-agent-smoke-') as temp:
        root = Path(temp)
        database = root / 'isolated data' / 'jobs.sqlite3'
        profile = {'name': 'Packaging test', 'keywords': 'automation'}
        with launch(executable, database, root / 'startup.log') as (process, origin):
            wait_until_ready(process, origin)
            for path, expected in (
                ('/', 'text/html'), ('/style.css', 'text/css'), ('/app.js', 'text/javascript'),
                ('/profile.js', 'text/javascript'), ('/ai.js', 'text/javascript'),
            ):
                with request(origin, path) as response:
                    assert response.headers.get_content_type() == expected, path
                    assert response.read().strip(), f'Empty dashboard asset: {path}'
            with request(origin, '/api/jobs') as response:
                initial = json.load(response)
            assert initial['jobs'] == []
            with request(origin, '/api/profile', profile, initial['token']) as response:
                assert response.status == 200

        with launch(executable, database, root / 'restart.log') as (process, origin):
            wait_until_ready(process, origin)
            with request(origin, '/api/profile') as response:
                saved = json.load(response)['profile']
            assert {key: saved[key] for key in profile} == profile
        print('Packaged launcher served the dashboard and preserved the test profile after restart.')


if __name__ == '__main__':
    main()
